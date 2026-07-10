# modules/system_control.py
"""
J.A.R.V.I.S. - Controle do Sistema v2.0
Volume (pycaw) + brilho + bateria + info + processos.
"""

import subprocess
import platform
import psutil
from datetime import datetime

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from utils.logger import setup_logger

logger = setup_logger("system_control")


class SystemControl:
    """Controla funcoes do sistema operacional."""

    @staticmethod
    def get_system_info():
        info = {
            "os": platform.system(),
            "os_version": platform.version(),
            "machine": platform.machine(),
            "processor": platform.processor(),
            "cpu_percent": psutil.cpu_percent(interval=1),
            "ram_total_gb": round(psutil.virtual_memory().total / (1024**3), 2),
            "ram_used_percent": psutil.virtual_memory().percent,
            "disk_total_gb": round(psutil.disk_usage('/').total / (1024**3), 2),
            "disk_used_percent": psutil.disk_usage('/').percent,
        }
        battery = psutil.sensors_battery()
        if battery:
            info["battery_percent"] = battery.percent
            info["battery_plugged"] = battery.power_plugged
        return info

    @staticmethod
    def get_cpu_usage():
        return psutil.cpu_percent(interval=1)

    @staticmethod
    def get_ram_usage():
        mem = psutil.virtual_memory()
        return {
            "total_gb": round(mem.total / (1024**3), 2),
            "used_gb": round(mem.used / (1024**3), 2),
            "percent": mem.percent
        }

    @staticmethod
    def get_battery_info():
        battery = psutil.sensors_battery()
        if battery:
            return {
                "percent": battery.percent,
                "plugged": battery.power_plugged,
            }
        return None

    @staticmethod
    def set_volume(nivel):
        """Ajusta volume do sistema."""
        nivel = max(0, min(100, int(nivel)))

        # Metodo 1: pycaw
        try:
            from ctypes import cast, POINTER
            from comtypes import CLSCTX_ALL
            from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume

            devices = AudioUtilities.GetSpeakers()
            interface = devices.Activate(
                IAudioEndpointVolume._iid_, CLSCTX_ALL, None
            )
            volume = cast(interface, POINTER(IAudioEndpointVolume))

            scalar = nivel / 100.0
            volume.SetMasterVolumeLevelScalar(scalar, None)

            if nivel == 0:
                volume.SetMute(1, None)
            else:
                volume.SetMute(0, None)

            logger.info(f"Volume ajustado para {nivel}% (pycaw)")
            return True
        except Exception as e:
            logger.warning(f"pycaw falhou: {e}")

        # Metodo 2: nircmd
        try:
            nivel_nircmd = int((nivel / 100) * 65535)
            subprocess.run(
                f"nircmd setsysvolume {nivel_nircmd}",
                shell=True, capture_output=True, timeout=2
            )
            logger.info(f"Volume ajustado para {nivel}% (nircmd)")
            return True
        except Exception:
            pass

        # Metodo 3: PowerShell
        try:
            ps_script = f"""
            Add-Type -TypeDefinition @"
            using System.Runtime.InteropServices;
            [Guid("5CDF2C82-841E-4546-9722-0CF74078229A"), InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
            interface IAudioEndpointVolume {{
                int f(); int g(); int h(); int i();
                int SetMasterVolumeLevelScalar(float fLevel, System.Guid pguidEventContext);
                int j();
                int GetMasterVolumeLevelScalar(out float pfLevel);
            }}
            [Guid("D666063F-1587-4E43-81F1-B948E807363F"), InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
            interface IMMDevice {{
                int Activate(ref System.Guid id, int clsCtx, int activationParams, out IAudioEndpointVolume aev);
            }}
            [Guid("A95664D2-9614-4F35-A746-DE8DB63617E6"), InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
            interface IMMDeviceEnumerator {{
                int GetDefaultAudioEndpoint(int dataFlow, int role, out IMMDevice endpoint);
            }}
            [ComImport, Guid("BCDE0395-E52F-467C-8E3D-C4579291692E")] class MMDeviceEnumeratorComObject {{ }}
            public class Audio {{
                static IAudioEndpointVolume Vol() {{
                    var enumerator = new MMDeviceEnumeratorComObject() as IMMDeviceEnumerator;
                    IMMDevice dev = null;
                    Marshal.ThrowExceptionForHR(enumerator.GetDefaultAudioEndpoint(0, 1, out dev));
                    IAudioEndpointVolume epv = null;
                    var epvid = typeof(IAudioEndpointVolume).GUID;
                    Marshal.ThrowExceptionForHR(dev.Activate(ref epvid, 23, 0, out epv));
                    return epv;
                }}
                public static float Volume {{
                    get {{ float v = -1; Marshal.ThrowExceptionForHR(Vol().GetMasterVolumeLevelScalar(out v)); return v; }}
                    set {{ Marshal.ThrowExceptionForHR(Vol().SetMasterVolumeLevelScalar(value, System.Guid.Empty)); }}
                }}
            }}
"@
            [Audio]::Volume = {nivel / 100.0}
            """
            subprocess.run(
                ["powershell", "-NoProfile", "-Command", ps_script],
                capture_output=True, timeout=5
            )
            return True
        except Exception:
            pass

        logger.error("Nenhum metodo de volume funcionou")
        return False

    @staticmethod
    def set_brightness(level):
        """Define brilho da tela."""
        try:
            import screen_brightness_control as sbc
            sbc.set_brightness(level)
            logger.info(f"Brilho definido para {level}%")
        except Exception as e:
            logger.error(f"Erro ao definir brilho: {e}")

    @staticmethod
    def lock_screen():
        """Bloqueia a tela."""
        try:
            import ctypes
            ctypes.windll.user32.LockWorkStation()
            logger.info("Tela bloqueada.")
        except Exception as e:
            logger.error(f"Erro ao bloquear tela: {e}")

    @staticmethod
    def shutdown_pc(delay=30):
        try:
            subprocess.run(["shutdown", "/s", "/t", str(delay)], check=True)
        except Exception as e:
            logger.error(f"Erro shutdown: {e}")

    @staticmethod
    def restart_pc(delay=30):
        try:
            subprocess.run(["shutdown", "/r", "/t", str(delay)], check=True)
        except Exception as e:
            logger.error(f"Erro restart: {e}")

    @staticmethod
    def cancel_shutdown():
        try:
            subprocess.run(["shutdown", "/a"], check=True)
        except Exception as e:
            logger.error(f"Erro cancelar shutdown: {e}")

    @staticmethod
    def get_running_processes(limit=10):
        processes = []
        for proc in psutil.process_iter(['name', 'cpu_percent', 'memory_percent']):
            try:
                processes.append(proc.info)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        processes.sort(key=lambda x: x.get('cpu_percent', 0) or 0, reverse=True)
        return processes[:limit]

    @staticmethod
    def kill_process(process_name):
        try:
            for proc in psutil.process_iter(['name']):
                if proc.info['name'] and process_name.lower() in proc.info['name'].lower():
                    proc.kill()
                    return True
            return False
        except Exception as e:
            logger.error(f"Erro kill process: {e}")
            return False