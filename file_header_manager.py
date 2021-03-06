'''
	The MIT License (MIT)

	Copyright (c) 2015 Vu. Le Thanh (thenewvu@gmail.com)

	Permission is hereby granted, free of charge, to any person obtaining a copy
	of this software and associated documentation files (the "Software"), to deal
	in the Software without restriction, including without limitation the rights
	to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
	copies of the Software, and to permit persons to whom the Software is
	furnished to do so, subject to the following conditions:

	The above copyright notice and this permission notice shall be included in all
	copies or substantial portions of the Software.

	THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
	IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
	FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
	AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
	LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
	OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
	SOFTWARE.
'''
import sublime
import sublime_plugin
import os
import fnmatch
import threading

settings = None

def log(message):
	print("[File Header Manager] %s" % message)


def update_file_header_in_file(filepath, new_header):
	_, ext = os.path.splitext(filepath)
	old_header_pattern = settings.get("old_header_patterns", {}).get(ext)
	new_header_pattern = settings.get("new_header_patterns", {}).get(ext)
	if (old_header_pattern is None) or (new_header_pattern is None):
		return

	log("Processing file: %s" % filepath)
	with open(filepath, "r+") as fstream:
		content = str(fstream.read())

		fstream.seek(0)
		fstream.truncate()
		fstream.seek(0)

		if not content.startswith(old_header_pattern["begin"]):
			log("Not found header. Add the new.")
			content = new_header_pattern["begin"] + "\n" + new_header + "\n" + new_header_pattern["end"] + "\n" + content
			fstream.write(content)
			return

		log("Found a header. Update it.")
		header_end_index = content.find(old_header_pattern["end"], len(old_header_pattern["begin"]))
		content = new_header_pattern["begin"] + "\n" + new_header + "\n" + new_header_pattern["end"] + "\n" + content[(header_end_index + len(old_header_pattern["end"])):]
		fstream.write(content)

def is_ignored_dirname(dirname):
	ignored_dirnames = settings.get("ignored_dirnames", [])
	for ignored_dirname in ignored_dirnames:
		if fnmatch.fnmatch(dirname, ignored_dirname):
			return True
	return False


def get_header_template_in_path(path):
	if os.path.isfile(path):
		return None

	template_filename = settings.get("header_template_filename", None)
	if template_filename is not None:
		template_filepath = os.path.join(path, template_filename)
		if os.path.exists(template_filepath):
			with open(template_filepath, "r") as fstream:
				return fstream.read()

	return None


def update_file_header_in_path(path):
	log("Starting update file header in %s." % path)

	default_header_template = settings.get("default_header_template", "This is the default header template.")
	header_template = get_header_template_in_path(path)
	if header_template is None:
		header_template = default_header_template

	if os.path.isfile(path):
		update_file_header_in_file(path, header_template)
	else:
		for root, dirs, files in os.walk(path):
			for dirname in dirs:
				if is_ignored_dirname(dirname):
					log("Ignore dirname %s." % dirname)
					dirs.remove(dirname)

			local_header_template = get_header_template_in_path(path)
			if local_header_template is None:
				local_header_template = header_template

			for filename in files:
				filepath = os.path.join(root, filename)
				update_file_header_in_file(filepath, local_header_template)


class UpdateFileHeaderCommand(sublime_plugin.TextCommand):
	def run(self, edit, paths):
		global settings
		settings = sublime.load_settings("file_header_manager.sublime-settings")
		for path in paths:
			threading.Thread(target=update_file_header_in_path, args=(path,)).start()

class UpdateFileHeaderInCurrentFileCommand(sublime_plugin.TextCommand):
	def run(self, edit):
		global settings
		settings = sublime.load_settings("file_header_manager.sublime-settings")
		threading.Thread(target=update_file_header_in_path, args=(self.view.file_name(),)).start()