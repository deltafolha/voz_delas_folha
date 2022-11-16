##################################################
###############      LOGGING      ################
##################################################



"""
	Este microserviço tem com objetivo automatizar os loggs gerados pelos 
	demais serviços do pyetlapp.
"""


""" Imports """

import logging
from functools import wraps
import datetime
import os


""" Configurations Variables """

pyetlpath = os.getcwd()



""" Class """
class Log:

	"""
	Ilustration:
			
			from log import	Log
			
			logger = Log('test_app',__name__)
			
			
			@logger.critical
			def request_api():
				logger.info("Start")

				r = requests.request(method,url, headers=api_headers, data=payload)

				if r.status_code == 200:
					data = r.json()['resource']['items']
					if data:
						return data
					else:
						return None
						logger.warning("Ausencia de dados")

				else:
					logger.cust_critical(f'status_code: {r.status_code}, falha na requisição.')

	

	Parameters:

			filename  (str): name para compor o path de destino ao arquivo .log.
			func_name (str): name da fuction que alimetará o decorater critical.

	

	
	Metodos:

			Os seguintes metodos tem com objetivo retorna os Logs de info, warning, customized critical e critical.
			
		
			Parameters:

					msg (str): messagem que retornará no Log.
				

			Returns:
					Info:
					[2021-07-02 11:38:10,927 INFO __main__] Inicio do processo

					Warning:
					[2021-07-02 12:19:18,282 WARNING __main__] Processo pausado

					Cust_Critical:
					[2021-07-02 12:16:54,425 CRITICAL __main__] Func:divide() | ERROR:CUSTOMIZED: O denominador não pode ser Zero!

					Critical
					[2021-07-02 12:14:34,306 CRITICAL __main__] Func:divide() | ERROR:division by zero

		
	"""



	def __init__(self, filename,func_name):
		
		date = datetime.datetime.now().replace(second=0, microsecond=0)

		self.path = os.path.join(*[pyetlpath, 'log', date.strftime('%Y'), date.strftime('%m'), date.strftime('%d')])        
		os.makedirs(self.path, exist_ok=True)
		
		file_log = os.path.join(*[self.path, filename+'_log_'+date.strftime('%Y%m%d')+'.log'])
		
		logging.basicConfig(filename=file_log, level=logging.INFO, filemode='a', format='[%(asctime)s %(levelname)s %(name)s] %(message)s')
		self.logger = logging.getLogger(func_name)


	""" Metodos """

	def info(self, msg):		
		self.logger.info(msg)



	def warning(self, msg):		
		self.logger.warning(msg)

	def cust_critical(self,msg):
		l_sms = f'CUSTOMIZED: {msg}'
		raise Exception(l_sms)


	def critical(self, func):
		@wraps(func)
		def inner(*args, **kwargs):
			try:
				result = func(*args, **kwargs)
				return result
			except (Exception) as e:
				l_sms = f'Func:{func.__name__}() | ERROR:{e}'
				self.logger.critical(l_sms)
		return inner       
