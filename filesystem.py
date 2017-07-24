# !/usr/bin/env python3
# -*- coding: utf-8 -*-
# Linux compatible #guitar

import os
import os.path as op
import shutil
import glob
import stat
import re

NEXT_DIRECTORY_CHARACTER = SEP = op.sep # / or \ (slash or backslash)
HOME = op.expanduser('~') # TODO: check in Windows
assert op.exists(HOME), "HOME directory must exist"

class _Item(object):
	"""Superclass for File and Directory classes"""

	def __init__(self, path, quiet=False):
		path = abspath(path)
		self._path = path
		self._name = op.split(path)[-1]
		if not op.exists(path) and not quiet:
			print("WARNING: {} still does not exist".format(self))

	def __repr__(self):
		return "_Item('{}')".format(self._path)

	def __str__(self):
		return "<_Item at '{}'>".format(self._path)

	def __bool__(self):
		return self.exist()

	def __nonzero__(self):
		return self.exist()

	def info(self):
		"""return standard os.stat metadata"""
		return info(self._path)

	def delete(self):
		"""remove existed"""
		assert self.exist(), "Cannot remove not existed {}".format(self)
		os.remove(self._path)

	def move(self, directory):
		"""move to directory"""
		assert self.exist(), "Cannot move not existed {}".format(self)
		new_path = concat(directory.path, self._name)
		shutil.move(self._path, new_path)
		self._path = new_path

	def copy(self, new_path):
		"""return copy with new path (including renaming)"""
		new_path = abspath(new_path)
		shutil.copy(self._path, new_path)
		return Item(new_path)

	def copy_to(self, directory, new_name=None):
		"""return copy to directory"""
		new_name = new_name or self._name
		new_path = concat(directory.path, new_name)
		return self.copy(new_path)

	def rename(self, new_name):
		"""rename with extension"""
		new_path = self._path[:self._path.rfind(SEP) + 1] + new_name
		os.rename(self._path, new_path)
		self._path = new_path
		self._name = new_name

	def exist(self):
		"""check if the file exists"""
		return op.exists(self._path)

	def get_size(self):
		"""return file size"""
		return op.getsize(self._path)

	def get_parent(self):
		"""return parent directory"""
		Directory(self._path.rsplit(SEP, maxsplit=1)[0])

	def hardlink(self, directory, name=None):
		"""create hard link in directory"""
		name = name or self._name
		path = concat(directory.path, name)
		assert path != self._path, "Cannot create hard link with the same path '{}'".format(path)
		os.link(self._path, path)
		return Item(path)

	def symlink(self, directory, name=None):
		"""create symbolic (standard) link in directory"""
		name = name or self._name
		path = concat(directory.path, name)
		assert path != self._path, "Cannot create symbolic link with the same path '{}'".format(path)
		os.symlink(self._path, path)
		return Item(path)

	def chown(self, uid, gid):
		"""NOTE (on the comp):
		0 -- root, 1000 -- vanfed, 1001 -- sauron"""
		os.chown(self._path, uid, gid)

	@property
	def name(self):
		return self._name

	@name.setter
	def name(self, new_name):
		self.rename(new_name)

	@property
	def path(self):
		return self._path

	@path.setter
	def path(self, new_path):
		new_path = abspath(new_path)
		shutil.move(self._path, new_path)
		self._name = op.split(new_path)[-1]
		self._path = new_path

	@property
	def directory(self):
		return self.get_parent()

	@directory.setter
	def directory(self, new_directory):
		assert isinstance(new_directory, Directory), "not a Directory"
		self.move(new_directory)

	@property
	def size(self):
		return self.get_size()

	@size.setter
	def size(self, smth):
		raise TypeError("size does not support assignment")


class File(_Item):
	"""Class for fast editing text files and manipulating with them"""

	def __init__(self, path, quiet=False):
		_Item.__init__(self, path, quiet)
		self._ext = self.get_ext() # without dot
		self.text_io_wrapper = None

	def __repr__(self):
		return "File('{}')".format(self._path)

	def __str__(self):
		return "<File at '{}'>".format(self._path)

	def __iter__(self):
		return iter(self.get_text())

	def __contains__(self, x):
		return x in self.get_text()

	def __getitem__(self, number):
		return self.get_text()[number]

	def __setitem__(self, number, value):
		text = self.get_text()
		self.set_text(text[:number]+str(value)+text[number+1:])

	def __len__(self):
		"""len of text (chars) in text file"""
		return self.len()

	def len(self):
		"""len of text (chars) in text file"""
		assert self.exist(), "not existed {} has no len".format(self)
		return len(open(self._path).read())

	def strlen(self):
		"""number of strings in text file"""
		assert self.exist(), "not existed {} has no strlen".format(self)
		return len(open(self._path).readlines())

	def create(self):
		"""create empty text file"""
		self.set_text('')

	def clear(self):
		"""empty existed text file"""
		assert self.exist(), "cannot clear not existed {}".format(self)
		self.set_text('')

	def rename(self, new_name, with_ext=True):
		"""rename the file"""
		if not with_ext:
			new_name += '.' + self._ext
		_Item.rename(self, new_name)
		self._ext = self.get_ext()

	def open_file(self, mode='r', encoding=None):
		self.text_io_wrapper = open(self._path, mode, encoding=encoding)
		return self.text_io_wrapper

	def close_file(self):
		self.text_io_wrapper.close()
		self.text_io_wrapper = None

	def get_text(self, encoding=None):
		"""return whole text of the text file"""
		with open(self._path, 'r', encoding=encoding) as file:
			text = file.read()
		return text

	def set_text(self, new_text, encoding=None):
		"""set text of the text file"""
		with open(self._path, 'w', encoding=encoding) as file:
			file.write(new_text)

	def print_text(self):
		"""print text of the text file"""
		print(self.get_text())

	def get_ext(self):
		"""return file extension without dot"""
		return op.splitext(self._name)[1][1:]

	def splitext(self):
		"""return tuple ('<name>', '.<ext>'')"""
		return op.splitext(self._name)

	def chmod(self, mode):
		"""for example: mode='-rwxrx---x' (3 '-'-position on every field)
		where 'rw' means 'read and write', 'r' means 'read only',
		'w' means 'write only', '---' means 'no access',
		'x' means 'executable. Order: '-<owner><group><other>' -- Unix 'ls -l'-like syntax."""
		# + see http://www.computerhope.com/unix/uchmod.htm
		mode = mode[1:]
		ugo = [0, 0, 0] # oct 0o000
		corresponds = {'-': 0, 'x': 1, 'w': 2, 'r': 4}
		for i, m in enumerate([mode[i: i + 3] for i in range(0, len(mode), 3)]):
			for ch in m:
				ugo[i] += corresponds[ch]
		os.chmod(self._path, int("{}{}{}".format(*ugo), 8))

	def __extract(self, directory=None):
		"""TODO:
		extract archive (by default: in parent directory)"""
		if directory is None:
			directory = self._path[:self.name.rfind(SEP)]
		# return Directory(...)

	def find(self, string, every=False, quiet=True):
		"""return index of '<reg exp>' in the file or indexes;
		if 'every' == True return indexes"""
		text = self.get_text()
		result = text.find(string)
		if result == -1 and not quiet:
				print("String {} was not found, -1 returned.".format(string))
		if not every:
			return result
		else:
			results = []
			while result != -1:
				results.append(result)
				result = text.find(string, result)
			return results

	def crop(self, *pairs, coherent=False, quiet=True):
		"""cut specified text from the file;
		 'pairs' =  iterator of (start, end);
		 'start' and 'end' may be both strings and numbers;
		 'coherent' means one just after another"""
		text = self.get_text()
		start = end = 0
		for pair in pairs:
			# initialization 'start'
			if isinstance(pair[0], str):
				if coherent:
					start = text.find(pair[0], start)
				else:
					start = text.find(pair[0])
			elif isinstance(pair[0], int):
				start = pair[0]
			# initialization 'end'
			if isinstance(pair[1], str):
				if coherent:
					end = text.find(pair[1], max(start + 1, end))
				else:
					end = text.find(pair[1], start + 1)
			elif isinstance(pair[1], int):
				end = pair[1]
			if not quiet:
				print("Pair prepared: ({0[0]}, {0[1]}) --> ({1}, {2}).".format(pair, start, end))
			# cropping
			if -1 < start < end < len(text):
				if not quiet:
					print("Cutted [{0}:{1}]:\n'{2}'".format(start, end, text[start:end]))
					print(text[start:end])
				text = text[:start] + text[end:]
			elif not quiet:
				print("For the pair ({0[0]}, {0[1]}) (= ({1}, {2})) nothing cutted.".format(pair, start, end))
		self.set_text(text)

	def remove(self, *args, quiet=True):
		"""remove strings;
		'args' = iterator of ('<string>' [, <number of removings>])"""
		text = self.get_text()
		for arg in args:
			if isinstance(arg[0], str):
				string = arg[0]
			else:
				position = arg[0]
			if len(arg) == 2:
				number = -arg[1]
				if not isinstance(number, int):
					if not quiet:
						print("Wrong number format: '{0}'. Replaced with 'None'.".format(number))
					number = None
			else:
				number = None
			if isinstance(arg[0], str):
				position = text.find(string)
			if not quiet and position == -1:
					print("There is not at all '{0}'.".format(string))
			while position != -1 and (number is None or number < 0):
				if not quiet:
					print("Removed {0} in {1} position.".format(string, position))
				text = text[:position] + text[position + len(string):]
				if number != None:
					number += 1
				position = text.find(string, position)
			if not quiet and position != -1:
				print("There are at least one more matches with '{0}'.".format(string))
		self.set_text(text)

	def replace(self, *pairs, quiet=True):
		"""replace old strings (not whole) with new ones in the file;
		'pairs' = iterator of ('<old>', '<new>' [, <number of replacings>])"""
		text = self.get_text()
		for pair in pairs:
			(old, new) = (pair[0], pair[1])
			if len(pair) == 3:
				number = -pair[2]
				if not isinstance(number, int):
					if not quiet:
						print("Wrong number format: '{0}'. Replaced with 'None'.".format(number))
					number = None
			else:
				number = None
			old_position = text.find(old)
			if not quiet and old_position == -1:
					print("There is not at all '{0}'.".format(old))
			while old_position != -1 and (number is None or number < 0):
				if not quiet:
					print("Replaced {0} with {1} in {2} position.".format(old, new, old_position))
				text = text[:old_position] + new + text[old_position + len(old):]
				if number != None:
					number += 1
				old_position = text.find(old, old_position + len(new))
			if not quiet and old_position != -1:
				print("There are at least one more matches with '{0}'.".format(old))
		self.set_text(text)

	def replace_strings(self, *pairs, quiet=True):
		"""replace old whole strings with new ones in the file;
		'pairs' = iterator of ('<old>', '<new>' [, <number of replacings>])"""
		text = self.get_text()
		for pair in pairs:
			(old, new) = (pair[0], pair[1])
			if len(pair) == 3:
				number = -pair[2]
				if not isinstance(number, int):
					if not quiet:
						print("Wrong number format: '{0}'. Replaced with 'None'.".format(number))
					number = None
			else:
				number = None
			old_position = text.find(old)
			start = text.rfind('\n', 0, old_position) + 1
			end = text.find('\n', old_position)
			if not quiet and old_position == -1:
					print("There is not at all '{0}'.".format(old))
			while old_position != -1 and (number is None or number < 0):
				if not quiet:
					print("Replaced {0} with {1} at {2} string.".format(text[start:end], new, text[:start].count('\n')+1))
				text = text[:start] + new + text[end:]
				if number != None:
					number += 1
				old_position = text.find(old, end)
			if not quiet and old_position != -1:
				print("There are at least one more matches with '{0}'.".format(old))
		self.set_text(text)


	def insert(self, new_text, position):
		"""insert text from the position into the text file"""
		text = self.get_text()
		text = text[:position] + new_text + text[position:]
		self.set_text(text)

	def __iadd__(self, s):
		self.append(s)

	def append(self, next_text):
		"""add the text to the end of the text file"""
		text = self.get_text()
		text += next_text
		self.set_text(text)

	def __find_and_apply(self, string, func): #TODO: check
		"""TODO:
		apply func to every found string (RegExp) in the text file"""
		text = self.get_text()
		di = 0 # shift
		for string_i in self.find(string, every=True):
			old = text[string_i + di:string_i + len(string) + di]
			new = func(old) 
			text = text[:string_i + di] + new + text[di + string_i + len(string) + 1:]
			di += len(new) - len(old)
		self.set_text(text)

	def __form(self, sign='long'):
		"""TODO:
		Format file with Python standards.
		'Sign' could be 'long', 'short' (without **//|^%@), or 'supershort' (just with <=>), or 'same' (do nothing).
					   (a /= b) (a + b, but a*b)            (a+b, but a > b)
		"""
		text = self.get_text()
		# TODO: check
		# TODO: comment treating (?)
		# TODO:'"""'''" treating (!)
		# sign-spacing
		all_signs = '\\\(\)\[\]\{\}\'\"\?\.\,\;\:\#\$\`' + '\=\!\<\>' + '\+\-' + '\*\**\/\//\@\^\&\|\%'
		special_signs = '\\\(\)\[\]\{\}\'\"\?\.\,\;\:\#\$\`'
		nonspecial_signs = '\!\=\<\>' + '\+\-' + '\*\**\/\//\@\^\&\|\%'
		comparing_signs = '\!\=\<\>'
		plus_mines_signs = '\+\-'
		algebraic_signs = '\*\**\/\//\@\^\&\|\%'
		math_signs = plus_mines_signs + algebraic_signs
		if sign == 'long':
			# add last whitespace # 'a+b' --> 'a+ b', especially for ' ? '
			text = re.sub(r'([' + nonspecial_signs[2:] + '])([^\=\s\/\*])', r'\1 \2', text)
			# add first whitespace # 'a+b' --> 'a +b', especially for ' ?= '
			text = re.sub(r'([^\s' + nonspecial_signs + '])([' + nonspecial_signs + '])', r'\1 \2', text)
		elif sign == 'short':
			# add last whitespace # 'a+b' --> 'a+ b', especially for ' ? '
			text = re.sub(r'([' + comparing_signs + plus_mines_signs + '])([^\=\s])', r'\1 \2', text)
			# add first whitespace # 'a+b' --> 'a +b', especially for ' ?= '
			text = re.sub(r'([^\s' + nonspecial_signs + '])([' + comparing_signs + plus_mines_signs + '])', r'\1 \2', text)
			# remove last whitespace # 'a * b' --> 'a *b', especially for '?'
			text = re.sub(r'([' + algebraic_signs + '])([\s])', r'\1', text)
			# remove first whitespace # 'a * b' --> 'a* b', especially for '?='
			text = re.sub(r'([\s])([' + algebraic_signs + '])', r'\2', text)
		elif sign == 'supershort':
			# add last whitespace # 'a<b' --> 'a< b', especially for ' ? '
			text = re.sub(r'([^' + math_signs + '])([' + comparing_signs + '])([^\=\s])', r'\1\2 \3', text)
			# add first whitespace # 'a<b' --> 'a <b', especially for ' ?= '
			text = re.sub(r'([^\s' + math_signs + '])([' + comparing_signs + '])', r'\1 \2', text)
			# remove last whitespace # 'a + b' --> 'a +b', especially for '?'
			text = re.sub(r'([' + math_signs + '])([\s])', r'\1', text)
			# remove first whitespace # 'a + b' --> 'a+ b', especially for '?='
			text = re.sub(r'([\s])([' + math_signs + '])', r'\2', text)
		text = re.sub(r'([,:;])(\S)', r'\1 \2', text)
		text = re.sub(r'(if|elif|while)(\()', r'\1 (', text)
		text = re.sub(r'([^if|elif|while]) (\()', r'\1(', text)
		text = re.sub(r'(\S\([^\)\()]*)\ \=([^\)\()]*\))', r'\1\=\2', text)
		text = re.sub(r'(\S\([^\)\()]*)\=\ ([^\)\()]*\))', r'\1\=\2', text)
		# TODO: checking parenthness
		# TODO: checking tabs & spaces
		self.set_text(text)

	@property
	def ext(self):
		return self._ext

	@ext.setter
	def ext(self, new_ext):
		self.rename(self.splitext()[0] + '.' + new_ext)

	@property
	def text(self):
		return self.get_text()

	@text.setter
	def text(self, new_text):
		self.set_text(new_text)

class Directory(_Item):
	"""Class for fast manipulating with directories"""

	def __init__ (self, path, quiet=False):
		_Item.__init__(self, path, quiet)

	def __repr__(self):
		return "Directory('{}')".format(self._path)

	def __str__(self):
		return "<Directory at '{}'>".format(self._path)

	def __len__(self):
		"""return number of items inside"""
		return len(self.ls())

	def __iter__(self):
		return iter(self.get_items())

	def __contains__(self, x):
		return x in self.get_items()

	def __getitem__(self, name):
		path = concat(self._path, item_name)
		return Item(path)

	def __lshift__(self, item):
		item.move(self)

	def __rrshift__(self, item):
		item.move(self)

	def __iadd__(self, item):
		item.copy_to(self)

	def __isub__(self, item):
		item.delete()

	def get_paths(self):
		"""return list of paths of the items inside"""
		return [concat(self._path, name) for name in os.listdir(self._path)]

	def get_items(self):
		"""return list of the items inside"""
		return [Item(concat(self._path, name)) for name in os.listdir(self._path)]

	def get_names(self):
		"""return list of name of the items inside"""
		return os.listdir(self._path)

	def get_size(self):
		"""return size. Recursive a-la $ sudo du -sh <self._path>"""
		size = op.getsize(self._path)
		for path in self.get_paths():
			size += Item(path).get_size()
		return size

	def create(self):
		"""create empty directory"""
		os.mkdir(self._path)

	def group(self):
		"""return a group of the items inside"""
		return Group(*self.get_paths())

	def delete(self):
		"""recursively remove the directory"""
		shutil.rmtree(self._path)

	def chmod(self, mode):
		"""for example: mode='-cal-al--l' (3 '-'-position on every field)
		where 'a' means 'access only', 'c' means 'create and delete only',
		'l' means 'list only', '---' means 'no access'.
		Order: '-<owner><group><other>'."""
		# + see http://www.computerhope.com/unix/uchmod.htm
		mode = mode[1:]
		ugo = [0, 0, 0] # oct 0o000
		corresponds = {'-': 0, 'a': 1, 'c': 2, 'l': 4}
		for i, m in enumerate([mode[i: i+3] for i in range(0, len(mode), 3)]):
			for ch in m:
				ugo[i] += corresponds[ch]
		os.chmod(self._path, int("{}{}{}".format(*ugo), 8))

	def chmod_inside(self, filemode=None, dirmode=None):
		"""for example: filemode='-rwxr-x--x' -- Unix 'ls -l'-like syntax;
		dirmode='-cal-al--l' (create and delete, access, list)."""
		for item in self.get_items():
			if filemode is not None and isinstance(item, File):
				item.chmod(filemode)
			if dirmode is not None and isinstance(item, Directory):
				item.chmod(dirmode)
				item.chmod_inside(filemode, dirmode)

	def chown_inside(self, uid, gid):
		"""NOTE: (on the comp)
		0 -- root, 1000 -- vanfed, 1001 -- sauron"""
		for item in self.get_items():
			item.chown(uid, gid)
			if isinstance(item, Directory):
				item.chown_inside(uid, gid)

	def empty(self):
		"""remove all the items inside"""
		self.delete()
		self.create()

	def remove(self, *names, quiet=False):
		"""remove all the items inside with given names"""
		for name in names:
			path = concat(self._path, name)
			if name in self.ls():
				Item(path).delete()
			elif not quiet:
				print("WARNING: '{}'' not in {}.".format(name, self))

	def insert(self, *paths, quiet=False):
		"""copy items with the paths link treat as directories"""
		for path in paths:
			item = Item(path)
			if item.exist():
				if item.name in self.ls():
					if not quiet:
						print("WARNING: {} is in {}!".format(item, self))
					index = 1
					new_name = item.name + '_' + str(index)
					while new_name in self.ls():
						index += 1
						new_name = item.name + '_' + str(index)
					if not quiet:
						print("WARNING: {} renamed to '{}' and pasted.".format(item, new_name))
				item.copy_to(self, new_name)
			else:
				if not quiet:
					raise FileNotFoundError("Unidentified input item {}!".format(item))

	def up(self):
		"""return upper directory"""
		return Directory(self._path[:self._path.rfind(self._name) - 1])

	def down(self, name):
		"""return the item inside with given name"""
		path = concat(self._path, item_name)
		return Item(path)

	def choose(self, number):
		"""return the item inside with given number in 'ls'-list"""
		return self.down(self.ls()[number])

	def cd(self, quiet=False):
		"""set the directory as current"""
		cd(self._path, quiet=quiet)

	def ls(self):
		"""return list of names of the items inside"""
		return sorted(os.listdir(self._path))

	@property
	def paths(self):
		return self.get_paths()

	@paths.setter
	def paths(self, *smth):
		raise TypeError("'paths' does not support assignment")

	@property
	def names(self):
		return self.get_names()

	@names.setter
	def names(self, *smth):
		raise TypeError("'names' does not support assignment")

	@property
	def items(self):
		return self.get_items()

	@items.setter
	def items(self, *smth):
		raise TypeError("'items' does not support assignment")

	@property
	def size(self):
		return self.get_size()

	@size.setter
	def size(self, smth):
		raise TypeError("'size' does not support assignment")

class Group(set):
	"""Group of files and/or directories, subclass of set"""

	def __init__(self, *paths, name='untitled'):
		set.__init__(self, *[Item(path) for path in paths])
		self._name = name

	def __str__(self):
		return "<Group '{}'>".format(self._name)

	def get_paths(self):
		"""return list of items' paths"""
		return [item.path for item in self]

	def get_items(self):
		"""return list of items"""
		return self

	def get_names(self):
		"""return list of items' names"""
		return [item.name for item in self]

	def get_size(self):
		size = 0
		for item in self:
			size += item.get_size()

	def __getitem__(self, name):
		return [item for item in self if item.name == name]

	def get(self, name):
		return [item for item in self if item.name == name]

	def copy(self, new_name=None):
		"""return copy of the group with new name"""
		new_name = new_name or ("Copy of " + self._name)
		return Group(*self.get_paths(), name=new_name)

	def split(self, func):
		"""split this group with the function"""
		subgroups = []
		results = {func(item) for item in self}
		for result in results:
			subgroup = Group(*[item.path for item in self if func(item) == result],
				name="splited with {}".format(func.__name__))
			subgroups.append(subgroup)
		return subgroups

	def strip(self, rule=None):
		"""remove the items if rule(<item>) return False,
		default: rule = lambda x: x.exist()"""
		rule = rule or (lambda x: x.exist())
		self -= self.cut(rule)

	def cut(self, rule):
		"""return new group of the items in the group if rule(<item>) return False"""
		cutted = {item for item in self if not rule(item)}
		self -= cutted
		return Group(*cutted, name="Scutted with rule {}.".format(rule.__name__))

	def apply(self, func, rule=None):
		"""apply func for every item in the group if rule(<item>) return True"""
		rule = rule or (lambda x: True)
		for item in self:
			if rule(item):
				func(item)

	def rename_all(self, func):
		"""rename every item with func(name)"""
		for item in self:
			item.rename(func(item.name))

	@property
	def size(self):
		return self.get_size()

	@size.setter
	def size(self, smth):
		raise TypeError("'size' does not support assignment")

	@property
	def paths(self):
		return self.get_paths()

	@paths.setter
	def paths(self, paths):
		self = Group(*paths, self._name)

	@property
	def items(self):
		return self

	@items.setter
	def items(self, items):
		self = Group(*[item.path for item in items], self._name)

# a few useful functions

def what_is(path, quiet=True):
	if isinstance(path, Group):
		if not quiet:
			print("It is a group of files and directories!")
		return "group"
	if isinstance(path, File) or isinstance(path, Directory):
		path = path.path
	answer = ''
	if op.islink(path):
		if not quiet:
			print("It is a symlink to '{}'! :$".format(op.realpath(path)))
		answer = "symlink to "
	if op.isfile(path):
		if not quiet:
			print("It is a file (or hard link)! :)")
		answer += "file"
	elif op.isdir(path):
		if not quiet:
			print("It is a directory! ;)")
		answer += "directory"
	return answer

def abspath(path):
	"""return absolute path"""
	if path[0] == '~':
		path = HOME + path[1:]
	return op.abspath(path)

def Item(path, quiet=False):
	"""return File or Directory with given path"""
	path = abspath(path)
	if op.exists(path):
		if op.isfile(path):
			return File(path)
		elif op.isdir(path):
			return Directory(path)
		elif op.islink(path):
			return File(path) if '.' in path.split(SEP)[-1] else Directory(path)
		else:
			raise ValueError("""Very strange case:
it exists but it is neither file, nor directory (and nor link, too)...
See path '{}'""".format(path))
	else:
		if not quiet:
			print("WARNING: path '{}' still does not exist".format(path))
		return File(path) if '.' in path.split(SEP)[-1] else Directory(path)

HOME_DIRECTORY = Directory('~')

def glob(path_pattern):
	"""search for files here with RegExp (glob)"""
	return glob.glob(path_pattern)

def info(path):
	"""return os.stat metadata"""
	return os.stat(path)

def down(name, directory_path='.'):
	"""return inner for the directory path item with the name"""
	path = concat(directory_path, name)
	return Item(path)

def choose(part_of_name='', directory_path='.', types=[File, Directory], quiet=False):
	"""return inner for the directory path item with the number"""
	variants = list(filter(lambda item: part_of_name in item.name and any([isinstance(item, t) for t in types]), Directory(directory_path).get_items()))
	variants.sort(key=lambda d: d.name) 
	if len(variants) == 1:
		return variants[0]
	elif len(variants) > 1:
		if not quiet:
			print("More than one matches")
			do_print = input("Print all {}? (y/n) ".format(len(variants)))
			if 'y' in do_print or do_print.strip() == '':
				print()
				for i, item in enumerate(variants):
					print(i, item)
				choice = input("Choose #? (#/n) ")
				if choice.isnumeric():
					return variants[int(choice)]
		return variants
	else:
		if not quiet:
			print('No matches')

def choose_input():
	return choose(*input().split(','))

def concat(*paths):
	"""concat(dir1_path, ..., file_path) --> dir1_path + SEP + file_path"""
	return SEP.join(paths)

def cd(place=None, quiet=False):
	"""set the directory path as current directory"""
	if place:
		if place[0] in (SEP, '~', '.', '..'):
			full_path = abspath(place)
		else:
			full_path = concat(abspath('.'), place)
		os.chdir(full_path)
		if not quiet:
			print(abspath('.'))
	else:
		cd_input()

def cd_input(autocompletion=True):
	if autocompletion:
		variants = choose(input(), types=[Directory])
		if isinstance(variants, Directory):
			cd(variants.path)

def cd_stairs_input(up_char='\\', all_char='*'):
	input_str = input()
	while input_str.strip() != '':
		if input_str[0] == up_char:
			if len(input_str) == input_str.count(up_char):
				up(input_str.count(up_char))
			else:
				cd(input_str[1:])
		else:
			if input_str == all_char:
				input_str = ''
			variants = choose(input_str, types=[Directory])
			if isinstance(variants, Directory):
				cd(variants.path)
		input_str = input()

def pwd():
	"""return working directory (path)"""
	return os.getcwd()

def cwd():
	"""return working directory (path)"""
	return os.getcwd()

def get_cd():
	"""return working directory (Directory instance)"""
	return Directory(os.getcwd())

def pd(quiet=False):
	"""cd to parent directory"""
	up(1, quiet)

def up(height=1, quiet=False):
	"""set upper directory of the current one"""
	for _ in range(height):
		if not quiet:
			cd('..')
		else:
			os.chdir(abspath('..'))

def mkdir(directory_path):
	"""create directory with the path"""
	os.mkdir(abspath(directory_path))

def rmdir(directory_path):
	"""remove just EMPTY directory with the path"""
	os.rmdir(abspath(directory_path))

def lsdir(directory_path, postfunction=None):
	"""list content of the directory with the path,
	postfunction by default is lambda x: x.name"""
	postfunction = postfunction or (lambda x: x.name)
	return [postfunction(item) for item in Directory(directory_path)]

def ls(postfunction=None):
	"""list content of the current directory,
	postfunction by default is lambda x: x.name"""
	postfunction = postfunction or (lambda x: x.name)
	return lsdir('.', postfunction=postfunction)

def unlock_pycache(path="/home/vanfed/Documents/Python/universal/__pycache__/filesystem.cpython-35.pyc"):
	"""root owned pycache pause syncing with dropbox"""
	File(path).chown(1000, 1000)