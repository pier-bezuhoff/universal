# -*- coding: utf-8 -*-
# python3 compatible
# ♑

from time import time, asctime
import random

# remember of timeit.timeit()

def print_attrs(instance, end='\n', sep=':\t'):
	for key in dir(instance):
		print(key + key_sep + str(getattr(instance, key)), end=end)

def on_instance(action=None):
	if action is None:
		action = lambda instance: print('instance created')
	def decorator(cls):
		def new_init(self, *args, **kwargs):
			instance = cls.__init__(self, *args, **kwargs)
			action(instance)
			return instance
		cls.__init__ = new_init
		return cls

def append_code(instance, method_name, code):
	"""`code` is func(self, *pargs, **kwargs)
	order: old_method(...); code(...)"""
	def new_method(self, *pargs, **kwargs):
		getattr(self, name)(*pargs, **kwargs)
		code(self, *pargs, **kwargs)
	setattr(instance, method_name, new_method)

def prepend_code(instance, method_name, code):
	"""`code` is func(self, *pargs, **kwargs)
	order: code(...); old_method(...)"""
	def new_method(self, *pargs, **kwargs):
		code(self, *pargs, **kwargs)
		getattr(self, name)(*pargs, **kwargs)
	setattr(instance, method_name, new_method)

def standard(func, arg_list=None, arg_dict=None, return_answer=True, print_output=True, repeat=0):
	"""useful wrapper for timing"""
	if arg_list is None:
		arg_list = []
	if arg_dict is None:
		arg_dict = {}
	output = ''
	start_time = time()
	result = func(*arg_list, **arg_dict)
	for _ in range(repeat):
		func(*arg_list, **arg_dict)
	end_time = time() - start_time
	output += """Wrapping function 'standard'.
Wrapped function \'{}\'.
Result: {}.
Estimated time: {}s
(current time: {}).""".format(func.__name__, result, end_time, asctime())
	if return_answer:
		output += '\n' + str(result)
	if print_output:
		print(output)
	else:
		return output

def repeater(func, arg_list=None, min=0, max=100, number=100,
	return_answer=False, print_output=True):
	"""?"""
	# QUESTION: why for
	output = ''
	if not arg_list:
		arg_list = [random.randint(min, max) for _ in range(number)]
	n = 0
	l = len(arg_list)
	result_list = []
	start_time = time()
	for arg in arg_list:
		result_list.append(func(arg))
	end_time = time() - start_time
	output += """Wrapping function 'repeater'.
Wrapped function \'{}\'.
Estimated time: {}s
average time: {}
(current time: {}).""".format(func.__name__, end_time,
		end_time/len(arg_list), asctime())
	output += "Sum: {}, number: {}, average: {}.".format(sum(result_list), l,
		1.0*sum(result_list)/l)
	if return_answer:
		output += '\n' + str(result_list)
	if print_output:
		print(output)
	else:
		return output

def comparator(func1, func2, arg_list=None, min=0, max=100, number=100,
	check_equal=False, print_output=True):
	"""?"""
	# QUESTION: why for
	output = ''
	output += "Wrapping function 'comparator'.\n"
	if not arg_list:
		arg_list = [random.randint(min, max) for _ in range(number)]
	start_time = time()
	for arg in arg_list:
		func1(arg)
	end_time = time() - start_time
	output += """Wrapped function \'{}\'; estimated time: {}s, average time: {}s.
	""".format(func1.__name__, end_time, end_time/len(arg_list))
	start_time = time()
	for arg in arg_list:
		func2(arg)
	end_time = time() - start_time
	output += """Wrapped function \'{}\'; estimated time: {}s, average time: {}s
	(current time: {}).""".format(func2.__name__, end_time,
		end_time/len(arg_list), asctime())
	if check_equal:
		for arg in arg_list:
			if func1(arg) != func2(arg):
				output += "\nNot always equal. For example at {}.".format(arg)
				break
		else:
			output += "\nEqual on the arg list."
	if print_output:
		print(output)
	else:
		return output

__all__ = ['standard', 'repeater', 'comparator']
