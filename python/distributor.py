
from stablediffusion import StableDiffusionInstance, StableDiffusionAPI
from dataclasses import dataclass
from uuid import uuid4

@dataclass
class DistributorInstance:
	sd_instances : list[StableDiffusionInstance] = None
	hash_id_cache : list[str] = None

class DistributorAPI:

	@staticmethod
	def check_stable_diffusion_instances( distributor : DistributorInstance ) -> list[StableDiffusionInstance]:
		unavailable_instances = []
		for instance in distributor.sd_instances:
			is_active = StableDiffusionAPI.is_sd_instance_online( instance )
			if not is_active:
				print("Stable Diffusion instance is unavailable: ", instance.url )
				unavailable_instances.append( instance ) # add to unavailable
				distributor.sd_instances.remove( instance ) # remove from active
		return unavailable_instances

	@staticmethod
	def distribute_text2img( distributor : DistributorInstance, parameters : dict ) -> str | None:
		return None

	@staticmethod
	def is_hash_ready( distributor : DistributorInstance, hash_id : str ) -> int:
		return -1

	@staticmethod
	def get_hash_id_image( distributor : DistributorInstance, hash_id : str, remove : bool = False ) -> str | None:
		pass

	@staticmethod
	def update_instances( distributor : DistributorInstance ) -> None:
		pass
