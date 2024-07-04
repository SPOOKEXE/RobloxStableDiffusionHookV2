
from network import main

import asyncio

if __name__ == '__main__':
	asyncio.run(main(host='0.0.0.0', port=5100, api_key=None))
