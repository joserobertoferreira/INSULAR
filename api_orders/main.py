from http import HTTPStatus

from auth.auth import Auth
from config import settings
from messages.download import DownloadMessages
from messages.process import ProcessMessages
from messages.receive import ListQueuedMessages


def api_orders() -> None:
    # Autentica na API e recupera o token
    authentication = Auth.login(
        settings.SERVER_BASE_ADDRESS,
        settings.API_USER,
        settings.API_PASSWORD,
    )

    # Verifica se houve sucesso na autenticação
    if authentication['HttpStatus'] == HTTPStatus.OK:
        headers = {
            'Authorization': 'Bearer ' + authentication['Token'],
            'Content-type': 'application/json',
        }

        # Recupera a lista de mensagens
        messageList = ListQueuedMessages.get_messages(
            settings.SERVER_BASE_ADDRESS,
            settings.RECEIVER,
            headers,
        )

        # Se houver mensagens na lista, faz o download
        if messageList['Errors'] == []:
            download = DownloadMessages(
                settings.SERVER_BASE_ADDRESS, headers, messageList['Messages']
            )

            messages = download.download_messages()

            # Se houve mensagens recuperadas, cria os ficheiros de encomendas
            if messages is not None:
                process = ProcessMessages(
                    settings.SERVER_BASE_ADDRESS, settings.FOLDER, headers
                )

                process.create_orders_files(messages)


if __name__ == '__main__':
    api_orders()
