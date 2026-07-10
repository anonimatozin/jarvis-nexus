"""
JARVIS - Exemplo de Integração com Universal Knowledge

Este arquivo mostra como integrar o Universal Knowledge no JARVIS principal.
Adicione este código ao seu main.py ou crie um novo módulo.
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.universal_knowledge import UniversalKnowledge


class JARVISWithKnowledge:
    def __init__(self):
        self.uk = UniversalKnowledge()
        self._setup_additional_modules()

    def _setup_additional_modules(self):
        # Adicione aqui módulos customizados
        pass

    def process_command(self, command: str) -> str:
        result = self.uk.process(command)

        if result["success"]:
            module = result["module"]
            action = result["action"]
            data = result["result"]

            if module == "gmail":
                return self._format_gmail_response(action, data)
            elif module == "calendar":
                return self._format_calendar_response(action, data)
            elif module == "github":
                return self._format_github_response(action, data)
            elif module == "system":
                return self._format_system_response(action, data)
            elif module == "web":
                return self._format_web_response(action, data)
            else:
                return f"Resultado: {data}"
        else:
            return result.get("message", "Não entendi o que você quer fazer")

    def _format_gmail_response(self, action: str, data) -> str:
        if action == "list":
            if not data:
                return "Sua caixa de entrada está vazia."
            response = f"Encontrei {len(data)} emails:\n"
            for email in data[:5]:
                response += f"• {email.get('subject', 'Sem assunto')} - {email.get('from', 'Desconhecido')}\n"
            return response
        elif action == "send":
            return "Email enviado com sucesso!"
        return str(data)

    def _format_calendar_response(self, action: str, data) -> str:
        if action == "today":
            if not data:
                return "Você não tem eventos hoje."
            response = f"Seus eventos de hoje:\n"
            for event in data:
                response += f"• {event.get('summary', 'Sem título')} - {event.get('start', '')}\n"
            return response
        elif action == "create":
            return f"Evento criado: {data.get('summary', '')}"
        return str(data)

    def _format_github_response(self, action: str, data) -> str:
        if action == "repos":
            if not data:
                return "Nenhum repositório encontrado."
            response = f"Seus repositórios:\n"
            for repo in data[:5]:
                response += f"• {repo.get('name', '')} - {repo.get('description', 'Sem descrição')}\n"
            return response
        return str(data)

    def _format_system_response(self, action: str, data) -> str:
        if action == "info":
            return (
                f"Sistema:\n"
                f"• CPU: {data.get('cpu_percent', 0)}%\n"
                f"• RAM: {data.get('memory_percent', 0)}%\n"
                f"• Processadores: {data.get('cpu_count', 0)}"
            )
        elif action == "cpu":
            return f"Uso de CPU: {data}%"
        elif action == "memory":
            return f"Uso de RAM: {data.get('percent', 0)}%"
        return str(data)

    def _format_web_response(self, action: str, data) -> str:
        if action == "weather":
            if "error" in data:
                return f"Erro ao buscar clima: {data['error']}"
            return (
                f"Clima em {data.get('city', '')}:\n"
                f"• Temperatura: {data.get('temp_c', '')}°C\n"
                f"• Condição: {data.get('description', '')}\n"
                f"• Umidade: {data.get('humidity', '')}%"
            )
        return str(data)

    def shutdown(self):
        self.uk.shutdown()


def main():
    jarvis = JARVISWithKnowledge()

    print("JARVIS Universal Knowledge pronto!")
    print("Digite 'sair' para encerrar.")
    print()

    while True:
        try:
            command = input("Você: ").strip()

            if command.lower() in ["sair", "exit", "quit"]:
                print("JARVIS: Até logo!")
                break

            if not command:
                continue

            response = jarvis.process_command(command)
            print(f"JARVIS: {response}")
            print()

        except KeyboardInterrupt:
            print("\nJARVIS: Até logo!")
            break
        except Exception as e:
            print(f"JARVIS: Erro - {str(e)}")

    jarvis.shutdown()


if __name__ == "__main__":
    main()
