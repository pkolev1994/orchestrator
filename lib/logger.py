import logging
import datetime
###custom libs
# from lib.containering import parse_config



class Logger:

	def __init__(self, filename, logger_name, dirname):
		"""
		Constructor
		Args:
			filename(str)
		Return:
			None

		Description of Log levels
		Level 	Numeric value
		CRITICAL 	50
		ERROR 	40
		WARNING 	30
		INFO 	20
		DEBUG 	10
		NOTSET 	0
		"""

		self.filename = filename
		self.logger_name = logger_name
		self.dir = dirname
		self.log = logging.getLogger(self.logger_name)
		self.log.propagate = False
		self.log.setLevel(10)
		# self.log.setLevel(parse_config("orchastrator.json")['logging_level'])
		self.fh = logging.FileHandler("{}{}_{:%Y%m%d%H}.log". \
									format(self.dir, self.filename, datetime.datetime.now()))
		self.formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
		self.fh.setFormatter(self.formatter)
		self.log.addHandler(self.fh)


	def debug(self, message):
		"""
		Logs in self.filename on all levels
		Args:
			message(str)
		Returns:
			None
		"""
		self.log.debug(message)

	def info(self, message):
		"""
		Logs in self.filename on info 20 level
		Args:
			message(str)
		Returns:
			None
		"""
		self.log.info(message)

	def warning(self, message):
		"""
		Logs in self.filename on info 30 level
		Args:
			message(str)
		Returns:
			None
		"""
		self.log.warning(message)

	def error(self, message):
		"""
		Logs in self.filename on info 40 level
		Args:
			message(str)
		Returns:
			None
		"""
		self.log.error(message)

	def critical(self, message):
		"""
		Logs in self.filename on info 50 level
		Args:
			message(str)
		Returns:
			None
		"""
		self.log.critical(message)

	def clear_handler(self):
		"""
		Args:
			None
		Returns:
			None
		"""
		if (self.log.hasHandlers()):
			self.log.handlers.clear()