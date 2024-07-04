
from network import main, Ngrok

import asyncio

async def main( ngrok : bool = False, port : int = 5100, api_key : str = None ) -> None:
	if ngrok is True:
		Ngrok.set_port(port)
		Ngrok.open_tunnel()
		print(f'Ngrok tunnel has been opened: {Ngrok.await_ngrok_addr()}')
	await main(host='0.0.0.0', port=port, api_key=api_key)
	if ngrok is True:
		Ngrok.close_tunnel()

if __name__ == '__main__':
	asyncio.run(
		main(ngrok=False, port=5100, api_key=None)
	)
