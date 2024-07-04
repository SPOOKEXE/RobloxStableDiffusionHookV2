from threading import Thread
from pyngrok import ngrok
from time import sleep

class Ngrok:
	'''
	Ngrok singleton class - manages the ngrok tunnel.
	'''
	port = 8080
	tunnel = None
	_thread = None

	@staticmethod
	def _internal_start_tunnel( port : int ) -> None:
		'''
		Connect to the ngrok servers with the given port.
		'''
		Ngrok.tunnel = ngrok.connect(port)

	@staticmethod
	def set_port( port : int ) -> None:
		'''
		Set the port.
		'''
		Ngrok.port = port

	@staticmethod
	def open_tunnel( ) -> None:
		'''
		Open the ngrok tunnel if it is not open already.
		'''
		assert Ngrok.tunnel == None, "Tunnel is already open (tunnel reference)."
		assert Ngrok._thread == None, "Tunnel is already open (thread exists)."
		Ngrok._thread = Thread(target=Ngrok._internal_start_tunnel, args=(Ngrok.port,), daemon=True)
		Ngrok._thread.start()
		if Ngrok.tunnel == None:
			print("Awaiting ngrok tunnel to start.")
			while Ngrok.tunnel == None:
				sleep(1)
		print("ngrok tunnel has started.")

	@staticmethod
	def close_tunnel( ) -> None:
		'''
		Close the ngrok tunnel if it is open.
		'''
		assert Ngrok.tunnel != None, "Tunnel is non-existent."
		Ngrok._thread = None
		ngrok.disconnect( Ngrok.get_ngrok_addr() )
		Ngrok.tunnel = None

	@staticmethod
	def get_ngrok_addr( ) -> str:
		'''
		Get the ngrok address for web requests.
		'''
		assert Ngrok.tunnel != None, "You must open the tunnel before you can get the address."
		return Ngrok.tunnel.public_url

	@staticmethod
	def await_ngrok_addr( ) -> str:
		while Ngrok.tunnel == None:
			sleep( 0.25 )
		return Ngrok.tunnel.public_url
