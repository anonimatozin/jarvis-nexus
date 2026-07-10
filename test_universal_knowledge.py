"""
JARVIS Universal Knowledge System - Teste e Demonstração

Execute este arquivo para testar o sistema:
python test_universal_knowledge.py
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.universal_knowledge import UniversalKnowledge


def main():
    print("=" * 60)
    print("JARVIS - Universal Knowledge System")
    print("=" * 60)
    print()

    jarvis = UniversalKnowledge()

    print("Status inicial:")
    status = jarvis.get_status()
    print(f"  Módulos registrados: {status['registered_modules']}")
    print(f"  Módulos ativos: {status['active_modules']}")
    print()

    test_commands = [
        "Ver meus emails",
        "Criar evento no calendário",
        "Listar meus repositórios no GitHub",
        "Ver uso de CPU",
        "Ver clima em São Paulo",
        "Abrir Google",
    ]

    print("Testando comandos:")
    print("-" * 60)

    for command in test_commands:
        print(f"\n> {command}")
        result = jarvis.process(command)

        if result["success"]:
            print(f"  ✓ Módulo: {result['module']}")
            print(f"  ✓ Ação: {result['action']}")
            print(f"  ✓ Resultado: {str(result['result'])[:100]}...")
        else:
            print(f"  ✗ {result['message']}")

    print()
    print("-" * 60)
    print("Status final:")
    status = jarvis.get_status()
    print(f"  Módulos ativos agora: {status['active_modules']}")
    print(f"  Stats conhecimento: {status['knowledge_stats']}")
    print()

    print("Aguardando 10 segundos para testar lazy loading...")
    import time
    time.sleep(10)

    print("Status após 10s (deveria desativar módulos ociosos):")
    status = jarvis.get_status()
    print(f"  Módulos ativos: {status['active_modules']}")

    jarvis.shutdown()
    print()
    print("Teste concluído!")


if __name__ == "__main__":
    main()
