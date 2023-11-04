
import os
import json

from threading import Thread
import traceback
from typing import Any
from stablediffusion import StableDiffusionInstance, StableDiffusionAPI
from dataclasses import dataclass
from uuid import uuid4
from enum import Enum
from time import sleep, time
from image import load_image_from_sd
from dataclasses import field
from math import floor

def array_find( array : list, value : Any ) -> int | None:
	try:
		return array.index( value )
	except:
		return None

def silent_pop_value( array : list, value : Any ) -> None:
	try:
		array.pop( array.index(value) )
	except:
		pass

def log_user_creation( user : str, data : dict, log_dir : str = "logs" ) -> None:
	os.makedirs( os.path.join( log_dir, user), exist_ok=True )

	timestamp = str(floor(time()))
	log_filepath = os.path.join( log_dir, user, f"{timestamp}.txt" )
	with open( log_filepath, 'w' ) as file:
		file.write( json.dumps({
			"requestee" : user,
			"info" : data.get('info') != None and json.loads( data.get('info') ) or None,
			"hash" : data.get('hash')
		}, indent=4) + "\n" )

	img_filepath = os.path.join( log_dir, user, f"{timestamp}.jpeg" )
	load_image_from_sd( data['images'][0] ).save( img_filepath )

class OperationStatus(Enum):
	NonExistent = -1
	InQueue = 0
	InProgress = 1
	Finished = 2
	Errored = 3

@dataclass
class DistributorInstance:
	sd_instances : list[StableDiffusionInstance] = field(default_factory=list)
	hash_id_cache : list[str] = field(default_factory=list)
	counter : int = 0

class DistributorAPI:

	@staticmethod
	def check_stable_diffusion_instances( distributor : DistributorInstance ) -> list[StableDiffusionInstance]:
		'''
		Check all the stable diffusion instances to see if they are available
		'''
		unavailable_instances = []
		for instance in distributor.sd_instances:
			is_active = StableDiffusionAPI.is_sd_instance_online( instance )
			if not is_active:
				print("Stable Diffusion instance is unavailable: ", instance.url )
				unavailable_instances.append( instance ) # add to unavailable
				distributor.sd_instances.remove( instance ) # remove from active
		return unavailable_instances

	@staticmethod
	def get_stable_diffusion_instance_infos( distributor : DistributorInstance ) -> list[dict]:
		# refresh the instance informations
		for instance in distributor.sd_instances:
			StableDiffusionAPI.refresh_sd_instance_info( instance )
		# pull all the information and return it
		return [ {
			"sys_info" : StableDiffusionAPI.get_sd_instance_system_info( instance )[1],
			"sd_info" : StableDiffusionAPI.get_sd_instance_info( instance )[1]
		} for instance in distributor.sd_instances ]

	@staticmethod
	def _internal_text2img( target_instance : StableDiffusionInstance, hash_id : str, parameters : dict ) -> None:
		try:

			# pop first because stable diffusion does not take the 'username' param
			try:
				userName = parameters.pop('username')
			except:
				pass

			success, data = StableDiffusionAPI.text2img( target_instance, parameters )

			# print(list(data.keys()))
			# TODO: support multiple images (batch_size / batch_count)?
			image = data['images'][0]

			if userName != None:
				try:
					data['hash_id'] = hash_id
					log_user_creation( userName, data )
				except Exception as exception:
					print('Failed to log user prompt: ')
					print( str(exception) )
			silent_pop_value(target_instance.queue, hash_id)
			target_instance.images[hash_id] = image
		except Exception as exception:
			target_instance.errored_ids.append( hash_id )
			print('Failed to post to server - error in processing.')
			print( traceback.format_exception( exception ) )
			success, data = False, 'Internal Server Error'
		if not success:
			# failed to distribute
			print('Distribution Warning:')
			print('Could not queue text2image in instance at ', target_instance.url)
			print( data )

	@staticmethod
	def distribute_text2img( distributor : DistributorInstance, parameters : dict, forceIndex : int = None ) -> str | None:
		if type(parameters) != dict:
			return False, 'Passed parameters value is not a dictionary'
		if type(forceIndex) != int and forceIndex != None:
			return False, 'ForceIndex must be an integer or None.'

		hash_id : str = uuid4().hex
		print('New hash for txt2img prompt: ', hash_id)

		# see if we can send it to an instance that is idle!
		available_instances = [ instance for instance in distributor.sd_instances if instance.busy == False ]
		if len(available_instances) == 0:
			# no idle instances, must queue it
			available_instances = distributor.sd_instances

		index = distributor.counter
		if forceIndex != None:
			index = min( max( forceIndex, 0 ), len(distributor.sd_instances) )

		# queue it in the target instance
		target_instance = available_instances[ index ]

		# internally send the text2img request
		target_instance.queue.append( hash_id )
		t = Thread(target=DistributorAPI._internal_text2img, args=(target_instance, hash_id, parameters, ), daemon=True)
		t.start()

		# increment the counter (and wrap it around)
		if forceIndex == None:
			distributor.counter += 1
			if distributor.counter > len(distributor.sd_instances) - 1:
				distributor.counter = 0

		# return hash to caller
		return hash_id

	@staticmethod
	def get_hash_id_sd_instance( distributor : DistributorInstance, hash_id : str ) -> StableDiffusionInstance | None:
		for instance in distributor.sd_instances:
			if instance.images.get( hash_id ) != None or array_find(instance.queue, hash_id ) != None:
				return instance
		return None

	@staticmethod
	def get_hash_status( distributor : DistributorInstance, hash_id : str ) -> int:
		# find the instance
		instance = DistributorAPI.get_hash_id_sd_instance( distributor, hash_id )
		if instance == None:
			return OperationStatus.NonExistent.value
		# determine the status
		if instance.images.get( hash_id ) != None:
			return OperationStatus.Finished.value
		elif len(instance.queue) > 0 and instance.queue[0] == hash_id:
			return OperationStatus.InProgress.value
		return OperationStatus.InQueue.value

	@staticmethod
	def get_hash_id_image( distributor : DistributorInstance, hash_id : str, pop_cache : bool = False ) -> str | None:
		instance = DistributorAPI.get_hash_id_sd_instance( distributor, hash_id )
		if (instance == None) or (instance.images.get( hash_id ) == None):
			return None
		if pop_cache: # pop it instead of just returning it
			return instance.images.pop(hash_id)
		return instance.images.get( hash_id )

	@staticmethod
	def get_operation_progress( distributor : DistributorInstance, hash_id : str ) -> dict | None:
		if DistributorAPI.get_hash_status( distributor, hash_id ) != OperationStatus.InProgress.value:
			return None
		instance = DistributorAPI.get_hash_id_sd_instance( distributor, hash_id )
		if (instance == None) or (len(instance.queue) == 0) or (instance.queue[0] != hash_id):
			return None
		# found the matching hash id that is in queue
		success, err = StableDiffusionAPI.get_sd_instance_progress( instance )
		if success:
			return err
		print('Get Operation Progress Error:')
		print('Could not get the progress of the current image at ', instance.url)
		print( err )
		return None

	@staticmethod
	def get_operation_queue_info( distributor : DistributorInstance, hash_id : str ) -> dict | None:
		if DistributorAPI.get_hash_status( distributor, hash_id ) != OperationStatus.InQueue.value:
			return None
		instance = DistributorAPI.get_hash_id_sd_instance( distributor, hash_id )
		if (instance == None) or (len(instance.queue) == 0) or (array_find(instance.queue, hash_id) == None):
			return None
		success, err = StableDiffusionAPI.get_sd_instance_queue_status( instance )
		if success:
			return err
		print('Get Operation Queue States Error:')
		print('Could not get the queue information of the stable diffusion instance at ', instance.url)
		print( err )
		return None
