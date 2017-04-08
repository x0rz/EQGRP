## @package ops.menu
# Menu API compatible with DSZ.
#
# Provides basic menu functionality for use within DSZ, as util.menu is not DSZ optimized.
#
# Functionality is a cross-combination of stuff found in the dsz.menu API, the util.menu API,
# and non-API menus found in DSKY, DF, and PC; all as a single package API. 
#
# This is meant to replace util.menu. However, the API is very different, so a drop in
# replacement is not possible.
#

from __future__ import print_function

import math
import numbers
import platform

if platform.python_version_tuple()[0] == '3':
    raw_input = input

__all__ = ["Menu"]

# This try/catch abuse let's us detect what platform we're on.
# Unfortunately, DSZ does not alter/expose anything via the "platform" module that'd make
# this easier.
_dsz_mode = False
try:
	import dsz
	import dsz.ui

	# Ensure DSZ functions when given Unicode. Acts as str() otherwise.
	def utf8(s):
		return s.encode("utf8") if type(s) is unicode else str(s)

	_dsz_mode = True
except ImportError: pass

# If the ip module is available, provide some more standard handlers.
_util_ip_mode = False
try:
	import ip
	_util_ip_mode = True
except ImportError: pass

## Default exit option text. Used multiple places, so defined here for easy updates.
EXIT = "Exit"

def _functiontype():
    pass

## Menu class
#
# With the extra functionality provided, an object provides a friendlier interface than
# a function call with very strict list/dict arguments would.
#
# No functionality is provided to re-order items after they're added, as this would add
# a lot of complexity for little gain as this is not a common desire. Use keyword filtering
# to make dynamically changing menus.
#
# One of the key functions pilfered both dsz.menu and util.menu is the menu option callback
# handler concept. Instead of mapping return values from the menu display, you can provide a
# function to call when the menu option is selected, allowing the menu handler to do the
# mapping. This works out especially well for menus with options that may change, either as
# the code updates with more content or the use of keyword filtering (also pilfered from
# dsz.menu) dynamically changing the content of the displayed menu (and therefore option
# ordering).
#
# Callbacks that wish to manipulate the menu state would probably be best implemented via
# a derived class, so they can easily and cleanly have a reference to the object.
#
# Stateful menus can be implemented two ways: a controllable heading block of text updated
# via a raw update function, or via stateful information provided for each menu option.
# The former requires the user code to manipulate and maintain the data, but also presents
# the data at the top of the menu before options as a configuration block. The latter
# requires use of callbacks to manipulate, but also presents the stateful information on
# the same line as the menu option, and each state text is aligned relative to other states
# within the same section.
#
# Users of this class will need only these two methods:
# - add_option() - this is the base method for populating your menu.
# - execute() - this will display and wait for input, and optionally loop until exit is selected.
#
# However, you can do more without adding your own extension code if you consider these methods
# which provide a default implementation for some common specialized tasks:
# - add_int_option() - integer input state.
# - add_hex_option() - integer input, but renders as hex.
# - add_str_option() - string input
# - add_toggle_option() - toggles between two states.
#
# One intended benefit of this class over the other implementations is the ability to change
# your menu type without re-implemeninting all of the user code to work with a different API.
#
# This class is probably not thread safe. On the other hand, DSZ doesn't support multi-threading.
#
# Use of this class can be automation friendly if default responses are filled in.
class Menu(object):

	def __init__(self):
		## Maintains a list of section names as provided so the order can be preserved
		# during display.
		self.__section_order = [""]
		## Maintains a mapping of section names to lists of content dictionaries.
		self.__section_content = {"": []}
		## Maintains the content of the overall heading.
		self.__heading = None
		## Current selection data.
		#
		# Only provides useful data during a callback function event. When that happens,
		# contains the content dictionary for the selection.
		self.__current = None
		## Curent content index; only useful during callback.
		self.__current_index = None
		## Current section index; only useful during callback.
		self.__current_section = None
		## Menu items from last call to display()
		self.__display = None
		## Output buffer cache.
		self.__output = None
		## Status for updating output buffer cache.
		self.__needs_update = True
	
	## Get section names.
	# \return List of section names, in display order.
	@property
	def sections(self):
		return self.__section_order
	
	## Gets the current selection data.
	#
	# \note This only has effect inside a callback function.
	@property
	def current(self):
		assert self.__current is not None, "This method can only be invoked from within a callback."
		return self.__current
	
	## Get the current selection's section.
	# \return Section name.
	@property
	def current_section(self):
		assert self.__current_section is not None, "This method can only be invoked from within a callback."
		return self.__current_section
	
	## Updates the current selection's option text.
	#
	# \param text
	#	New menu selection text.
	#
	# \note This only has effect inside a callback function.
	def set_current_text(self, text):
		assert self.__current_index is not None, "This method can only be invoked from within a callback."
		assert type(text) is str or type(text) is unicode, "text must be str or unicode"
		self.__section_content[self.__current_section][self.__current_index]["text"] = text
		self.__needs_update = True
	
	## Updates the current selection's state text.
	#
	# \param state
	#	New state text.
	#
	# \note This only has effect inside a callback function.
	def set_current_state(self, state):
		assert self.__current_index is not None, "This method can only be invoked from within a callback."
		self.__section_content[self.__current_section][self.__current_index]["state"] = state
		self.__needs_update = True
	
	## Updates the current selection's callback function.
	#
	# \param callback
	#	New callback function. Function is not executed during this callback phase.
	#
	# \note This only has effect inside a callback function.
	def set_current_callback(self, callback):
		assert self.__current_index is not None, "This method can only be invoked from within a callback."
		assert callable(callback), "callback must be a function"
		self.__section_content[self.__current_section][self.__current_index]["callback"] = callback
	
	## Updates the current selection's callback parameters.
	#
	# \param optdict
	#	Keyword arguments.
	#
	# \note If you change the callback parameters and don't have all the same keyword arguments
	# supplied, you may end up breaking your callback if default arguments are not supplied in
	# the callback definition.
	def set_current_cbparam(self, **optdict):
		assert self.__current_index is not None, "This method can only be invoked from within a callback."
		self.__section_content[self.__current_section][self._current_index]["cbparam"] = optdict
	
	## Updates the current selection's keywords.
	#
	# \param keywords
	#	New keyword list.
	#
	# \warning You are responsible  for maintaining your own sanity.
	def set_current_keywords(self, keywords):
		assert self.__current_index is not None, "This method can only be invoked from within a callback."
		assert type(keywords) is list, "keywords must be a list"
		self.__section_content[self.__current_index]["keywords"] = keywords
		self.__needs_update = True
	
	## Adds a section to the menu.
	#
	# Sections are ordered in the order they are first submitted. You do not need to
	# explicitly call this function, as add_option() will implicitly add a new section
	# when called with a section name not seen before.
	#
	# \param section
	#	Section name. Note the empty string ("") is treated as a special section for menus
	#	that do not desire section headers.
	#
	# \return True if the section was added, False otherwise. This might indicate the section
	# already exists.
	def add_section(self, section):
		assert type(section) is str or type(section) is unicode, "str or unicode string required"
		
		if section not in self.__section_order:
			self.__section_order.append(section)
			self.__section_content[section] = []
			self.__needs_update = True
			return True
		else:
			return False
	
	## Adds a menu option.
	#
	# Options are added to the specified section in the order they are submitted.
	#
	# \param option
	#	Option text.
	# \param section
	#	Section name. If left default ("") it will not have a section header and go
	#	into the implicit "first" section. If the section does not exist, it will
	#	be added.
	# \param keywords
	#	List of keywords for when this option should be displayed. Special case: the
	#	default empty list is an option that is always displayed, because otherwise
	#	the menu option could never be displayed.
	# \param callback
	#	Pointer to a callback function. The function may either take no arguments or
	#	a single dictionary argument. This function will be executed when the menu
	#	option is selected; unless you are not using execute() for menu input in
	#	which case you are reliant on whatever external implementation you're using.
	# \param state
	#	Optional text for use with menus where each option maintains a state (as opposed
	#	to a paragraph at the top of the menu). Manipulating state will require use of
	#	callbacks. The benefit of using state instead of updating the option text itself
	#	is that the display system will attempt to align state text per section in a clean way.
	# \param hex
	#	Set to true if state is storing a hex value. This will alter the display of the
	#	state content.
	# \param optdict
	#	Any addtional keyword arguments supplied are passed as-is to the specified callback
	#	function when this option is selected.
	def add_option(self, option, section="", keywords=[], callback=None, state=None, hex=False, **optdict):
		assert type(section) is str or type(section) is unicode, "str or unicode string required"
		assert type(option) is str or type(option) is unicode, "str or unicode string required"
		assert callback is None or type(callback) is type(_functiontype) or type(callback) is type(self.add_option), "callback must be a function, instancemethod, or None"
		
		self.add_section(section)
		self.__section_content[section].append({"text": option, "keywords": keywords, "callback": callback, "cbparam": optdict, "state": state, "hex": hex})
		
		self.__needs_update = True
	
	## A default callback mechanism for handling stateful menu options with string values.
	#
	# This is the function used by add_str_option(). When asking for input, the current
	# state is used as the default prompt response unless you set a diffrent default.
	#
	# \param allowempty
	#	Whether or not to allow empty strings as valid responses. If an empty string is
	#	returned, the input will loop. Note that when a menu state has a non-empty string
	#	and is used as the default response that it is impossible to obtain an empty
	#	string back.
	# \param default
	#	Set to None to do normal behavior of providing the current state as the default
	#	prompt response. Set to anything else, provides that text as the default. Note
	#	that if you want to allow empty strings as input you'll need to provide one as
	#	the default here, or you'll get the current state back.
	def callback_str(self, allowempty=False, default=None):
		result = None
		while True:
			result = self.__raw_input('New value for "%s"' % self.current["text"], self.current["state"] if default is None else default)
			if result or (result == "" and allowempty): break
		self.set_current_state(result)
	
	## Adds a string input stateful menu option.
	#
	# This will add a menu option that has a state, and uses a default callback function
	# to get new values for the state. This is provided as a convenience mechanism for
	# common tasks.
	#
	# \param option
	#	Option text.
	# \param state
	#	State text, not optional. Behaves the same as when state is supplied in add_option().
	# \param section
	#	Optional section name. See add_option() documentation.
	# \param keywords
	#	Optional keywords as used in add_option().
	# \param allowempty
	#	Whether or not to allow empty strings as valid responses. If an empty string is
	#	returned, the input will loop. Note that when a menu state has a non-empty string
	#	and is used as the default response that it is impossible to obtain an empty
	#	string back.
	# \param default
	#	Set to None to do normal behavior of providing the current state as the default
	#	prompt response. Set to anything else, provides that text as the default. Note
	#	that if you want to allow empty strings as input you'll need to provide one as
	#	the default here, or you'll get the current state back.
	def add_str_option(self, option, state, section="", keywords=[], allowempty=False, default=None):
		self.add_option(option=option, section=section, state=state, keywords=keywords, callback=self.callback_str, allowempty=allowempty, default=default)
	
	## A default callback mechanism for handling stateful menu options with integer values.
	#
	# This is the callback used by add_int_option().
	#
	# \param default
	#	Set to None to do normal behavior of providing the current state as the default
	#	prompt response. Set to anything else, provides that value as the default.
	def callback_int(self, default=None):
		self.set_current_state(self.__int_input('New value for "%s"' % self.current["text"], self.current["state"] if default is None else default))
	
	## Adds a integer input stateful menu option.
	#
	# This will add a menu option that has a state, and uses a default callback function
	# to get new values for the state. This is provided as a convenience mechanism for
	# common tasks.
	#
	# Input prompt accepts base-16 values when using the "0x" prefix.
	#
	# \param option
	#	Option text.
	# \param state
	#	State text, not optional. Behaves the same as when state is supplied in add_option().
	# \param section
	#	Optional section name. See add_option() documentation.
	# \param keywords
	#	Optional keywords as used in add_option().
	# \param default
	#	If not None, becomes the default prompt response for the integer input.
	def add_int_option(self, option, state, section="", keywords=[], default=None):
		assert isinstance(state, numbers.Integral), "State must be an integer."
		self.add_option(option=option, section=section, state=state, keywords=keywords, callback=self.callback_int, default=default)
		
	## A default callback mechanism for handling stateful menu options with hex values.
	#
	# \param default
	#	Set to None to do normal behavior of providing the current state as the default
	#	prompt response. Set to anything else, provides that value as the default.
	def callback_hex(self, default=None):
		defresponse = hex(self.current["state"]) if default is None else default
		if defresponse[-1] == 'L': defresponse = defresponse[0:-1]
		self.set_current_state(self.__int_input('New value for "%s":' % self.current["text"], defresponse))
	
	## Adds a hex input stateful menu option.
	#
	# \param option
	#	Option text.
	# \param state
	#	State text, not optional. Behaves the same as when state is supplied in add_option().
	# \param section
	#	Optional section name. See add_option() documentation.
	# \param keywords
	#	Optional keywords as used in add_option().
	# \param default
	#	If not None, becomes the default prompt response for the integer input.
	def add_hex_option(self, option, state, section="", keywords=[], default=None):
		assert isinstance(state, numbers.Integral), "State must be an integer."
		self.add_option(option=option, state=state, section=section, keywords=keywords, callback=self.callback_hex, default=default, hex=True)
	
	## A default callback mechanism for handling stateful options that toggle between two states.
	#
	# Switches option state to and from "enabled" and "disabled" states based on
	# the current state. The default text can be overridden to provide your own
	# state indications.
	#
	# \param enabled
	#	Enabled state.
	# \param disabled
	#	Disabled state.
	def callback_toggle(self, enabled="Enabled", disabled="<DISABLED>"):
		if self.current["state"] == enabled:
			self.set_current_state(disabled)
		else:
			self.set_current_state(enabled)
	
	## Adds a toggle state menu option.
	#
	# A toggle state menu option has two possible states and switches between
	# them when selected.
	#
	# \param option
	#	Option text.
	# \param state
	#	Optional starting state. If not supplied, option defaults to disabled.
	# \param section
	#	See add_option().
	# \param keywords
	#	See add_option().
	# \param enabled
	#	State text for enabled state.
	# \param disabled
	#	State text for disabled state.
	#
	# \see add_option
	def add_toggle_option(self, option, state=None, section="", keywords=[], enabled="Enabled", disabled="<DISABLED>"):
		assert state is None or state == enabled or state == disabled, "Starting state must be either enabled or disabled."
		self.add_option(option=option, state=state if state is not None else disabled, section=section, keywords=keywords, callback=self.callback_toggle, enabled=enabled, disabled=disabled)
	
	## Sets a content heading.
	#
	# This allows you to provide a content heading at the top of the menu. See
	# DSKY, DF, and PC menus for examples of why you might do this.
	#
	# If you want to dynamically update the heading, you'll have to maintain your
	# data and resubmit the entire heading with changed contents.
	#
	# Provide your own indents. A new line between the heading and the first menu
	# option will be automatically inserted.
	#
	# \param heading
	#	A string or a list of strings. If a list is provided, each element of the list
	#	will be a different line of the heading.
	def set_heading(self, heading):
		assert type(heading) is list or type(heading) is str or type(heading) is unicode, "Heading content must be list, str, or unicode"
		
		if type(heading) is str or type(heading) is unicode:
			self.__heading = [heading]
		else:
			self.__heading = heading
		
		self.__needs_update = True
	
	## Displays a menu and waits for user input.
	#
	# Optionally, this function can serve as the menu loop for situations where the menu
	# is presented again after each selection is made. Responses to selections then require
	# use of the callback feature to enable things to happen.
	#
	# \param prompt
	#	Prompt text.
	# \param default
	#	Default menu option. If provided, must be an integer between 0 and number of choices
	#	inclusive.
	# \param keywords
	#	Keyword filtering of menu items to show.
	# \param menuloop
	#	If set true, executes the menu loop instead of returning. On exit, will return. If
	#	set False, the menu will not loop, but will instead return after selection is made
	#	and callback (if implemented) has completed.
	# \param exit
	#	Provide optional text for option zero, the "exit" option. This should allow one to
	#	provide more clarity of what the exit option does; e.g. "Exit and do nothing" or
	#	"Exit with the configuration I just went through", etc. Might want to work on the
	#	phrasing for that last one.
	# \param exiton
	#	Optional list of menu selection numbers to exit on, besides the default exit option
	#	of zero. Note this only makes practical sense with a static menu or using options
	#	at the top of the menu so the selection value is unlikely to change. Has no effect
	#	unless menuloop is enabled, as otherwise all options technically "exit".
	#
	# \return Selection dictionary containing the following:
	# - \c selection - user's input
	# - \c option - option text
	# - \c option_state - option state text (or None)
	# - \c all_states - dictionary of sections, containing dictionaries of option texts with the state for that option.
	def execute(self, prompt="Enter selection", default=None, keywords=[], menuloop=True, exit=EXIT, exiton=[]):
		assert type(prompt) is str or type(prompt) is unicode, "Prompt must be str or unicode"
		assert type(menuloop) is bool, "Must be a Boolean state."
		assert type(exit) is str or type(exit) is unicode, "str or unicode required"
		assert default is None or type(default) is int, "Use None for no default or enter a valid integer."
		assert type(exiton) is list, "exiton must be a list"
		
		self.build_menu(keywords, exit)
		maxvalue = len(self.__display) - 1
		if type(default) is int:
			assert default >= 0 and default <= maxvalue, "Default value must be within range of options."
		
		if menuloop:
			result = -1
			exiton.append(0)
			while result not in exiton:
				# In DSZ mode, acknowledge "stop" requests sent to our "python" command.
				if _dsz_mode: dsz.script.CheckStop()
				self.display(keywords, exit)
				result = self.__menu_input(prompt, default, maxvalue)
				if result: self.__callback(self.__display[result][0], self.__display[result][2])
		else:
			self.display(keywords, exit)
			result = self.__menu_input(prompt, default, maxvalue)
			if result: self.__callback(self.__display[result][0], self.__display[result][2])
		
		# Build up exit state.
		exit_state = {
			"selection": result,
			"option": self.__display[result][1]["text"] if result != 0 else exit,
			"option_state": self.__display[result][1]["state"] if result != 0 else None,
			"all_states": self.all_states()
		}
		return exit_state
	
	## Returns state of all menu items that have states.
	def all_states(self):
		all = {}
		for s in self.__section_order:
			all[s] = {}
			for i in self.__section_content[s]:
				if i["state"]: all[s][i["text"]] = i["state"]
			# Probably not necessary, but it does reduce the data set you print out when debugging,
			# which could be helpful on menus with a bunch of sections but only one stateful section.
			if not all[s]:
				del all[s]
		return all
	
	## Displays the menu but does not interact with user.
	#
	# \param keywords
	#	List of keywords to show. Special case: items without keywords are displayed; or
	#	if this list is empty, all items are displayed.
	# \param exit
	#	Provide optional text for option zero, the "exit" option. This should allow one to
	#	provide more clarity of what the exit option does; e.g. "Exit and do nothing" or
	#	"Exit with the configuration I just went through", etc. Might want to work on the
	#	phrasing for that last one.
	def display(self, keywords=[], exit=EXIT):
		print(self.build_menu(keywords, exit))
	
	## Builds the menu output buffer.
	#
	# This builds and caches the output buffer for displaying the menu. If no updates are
	# made to any of the content via the API, then the buffer does not need to be updated
	# and can be returned from cache as-is, allowing for some modest performance gains with
	# static menus.
	#
	# Most users will want to use the display() or execute() methods; this is provided as
	# part of the public API for advanced users who want to consume the output into a
	# different system.
	#
	# \param keywords
	#	List of keywords to show. Special case: items without keywords are displayed; or
	#	if this list is empty, all items are displayed.
	# \param exit
	#	Provide optional text for option zero, the "exit" option. This should allow one to
	#	provide more clarity of what the exit option does; e.g. "Exit and do nothing" or
	#	"Exit with the configuration I just went through", etc. Might want to work on the
	#	phrasing for that last one.
	#
	# \return Output buffer string. Output encoding may be Unicode if any component
	# pieces used to build the string are unicode.
	def build_menu(self, keywords=[], exit=EXIT):
		assert type(keywords) is list
		assert type(exit) is str or type(exit) is unicode
		
		if not self.__needs_update: return self.__output

		# always starting with a newline to offset previous output.
		self.__output = "\n"
		if self.__heading:
			for i in self.__heading:
				self.__output += i + "\n"
			self.__output += "\n"
		# left padding for spacing the menu options evenly.
		lpad = str(int(math.log10(sum([len(i) for i in self.__section_content]) | 1)) + 3)
		self.__output += ("%" + lpad + "d) %s\n") % (0, exit)
		self.__display = [None]
		for s in self.__section_order:
			if s == "": self.__output += "\n"
			else: self.__output += "\n %s\n" % s
			
			# Find alignment for stateful options.
			longest = 0
			for i in self.__section_content[s]:
				if i["state"]:
					if len(i["text"]) > longest:
						longest = len(i["text"])
			
			# Build output buffer
			index = 0
			for i in self.__section_content[s]:
				# If no keywords supplied, show all.
				# If menu item has no keyword filter, show it.
				# If keywords supplied and item has keywords, then if one supplied keyword is in its filter then show it.
				if not keywords or not i["keywords"] or True in [k in keywords for k in i["keywords"]]:
					self.__output += ("%" + lpad + "d) %s") % (len(self.__display), i["text"])
					self.__display.append([s, i, index])
					if i["state"]:
						self.__output += " " * (longest - len(i["text"]))
						if i["hex"]:
							hexed = hex(i["state"])
							if hexed[-1] == "L": hexed = hexed[0:-1]
							self.__output += ": %s" % hexed
						else:
							self.__output += ": %s" % i["state"]
					self.__output += '\n'
				index += 1
					
		self.__needs_update = False
		
		return self.__output
	
	## Internal helper for handle callback scenarios.
	#
	# If there is no callback, just does nothing.
	#
	# If there is a callback and there are no callback parameters, calls
	# the callback with no arguments.
	#
	# If there is a callback and there is a parameter dictionary, passes the
	# parameter dictionary.
	#
	# \param section
	#	Section name.
	# \param index
	#	Content data index.
	def __callback(self, section, index):
		content = self.__section_content[section][index]
		if content["callback"] is not None:
			self.__current = content
			self.__current_index = index
			self.__current_section = section
			if content["cbparam"] is None:
				content["callback"]()
			else:
				content["callback"](**content["cbparam"])
			self.__current = None
			self.__current_index = None
			self.__current_section = None
	
	## Internal helper function to abstract input routines.
	#
	# \param prompt
	#	User prompt text.
	# \param default
	#	User default option.
	# \param maxvalue
	#	Maximum allowed input value.
	#
	# \return Integer menu selection value.
	def __menu_input(self, prompt, default, maxvalue):
		result = -1
		while result < 0 or result > maxvalue:
			result = self.__int_input(prompt, default)
		return result
	
	## Internal helper function to abstract raw input routines.
	#
	# \param prompt
	#	User prompt text.
	# \param default
	#	User default option. Set to None for no default.
	#
	# \return Raw input text string.
	def __raw_input(self, prompt, default):
		newprompt = prompt if prompt and prompt[-1] in [':', '?'] else prompt + ":"
		if _dsz_mode:
			return dsz.ui.GetString(utf8(newprompt), "" if default is None else utf8(default))
		else:
			value = raw_input((newprompt + " [%s] " % default) if default is not None else newprompt)
			if value == "" and default is not None: return default
			return value
	
	## Internal helper function to abstract integer input routines.
	#
	# \param prompt
	#	User prompt text.
	# \param default
	#	User default option. Set to None for no default.
	#
	# \return Integer input value.
	def __int_input(self, prompt, default):
		if _dsz_mode:
			newprompt = prompt if prompt and prompt[-1] in [':', '?'] else prompt + ":"
			return dsz.ui.GetInt(utf8(newprompt), "" if default is None else str(default))
		else:
			while True:
				value = self.__raw_input(prompt, default)
				if type(value) is int: return value
				try:
					if len(value) > 2 and value[0:2].lower() == "0x":
						return int(value, 16)
					else:
						return int(value)
				except ValueError: pass
	
	# These callback handlers and option helpers are only available if the util.ip module was available.
	if _util_ip_mode:
	
		## Default mechanism for handling IP address validation inputs.
		#
		# \param default
		#	If provided, will be the default value instead of the current state.
		def callback_ip(self, default=None):
			valid = False
			result = None
			while not valid:
				result = self.__raw_input('New IP address for "%s"' % self.current["text"], self.current["state"] if default is None else default)
				valid = util.ip.validate(result)
				if not valid:
					if _dsz_mode: dsz.ui.Echo("Invalid IP address.", dsz.ERROR)
					else: print("Invalid IPv4 or IPv6 address.")
			self.set_current_state(result)
		
		## Adds an IP address stateful option with IP validation.
		#
		# \param option
		#	Option text
		# \param section
		#	See add_option()
		# \param keywords
		#	See add_option()
		# \param ip
		#	IP address to default option to. If not provided, defaults to IPv4 localhost.
		# \param default
		#	Default prompt text to use instead of current state.
		def add_ip_option(self, option, section="", keywords=[], ip=None, default=None):
			assert ip is None or util.ip.validate(ip), "ip must be a valid IPv4 or IPv6 address, or None"
			self.add_option(option=option, section=section, state=ip, keywords=keywords, callback=self.callback_ip, default=default)
		
		## Default mechanism for handling IPv4 address validation inputs.
		#
		# \param default
		#	If provided, will be the default value instead of the current state.
		def callback_ipv4(self, default=None):
			valid = False
			result = None
			while not valid:
				result = self.__raw_input('New IPv4 address for "%s"' % self.current["text"], self.current["state"] if default is None else default)
				valid = util.ip.validate_ipv4(result)
				if not valid:
					if _dsz_mode: dsz.ui.Echo("Invalid IPv4 address.", dsz.ERROR)
					else: print("Invalid IP address.")
			self.set_current_state(result)
		
		## Adds an IPv4 address stateful option with IP validation.
		#
		# \param option
		#	Option text
		# \param section
		#	See add_option()
		# \param keywords
		#	See add_option()
		# \param ip
		#	IP address to default option to. If not provided, defaults to IPv4 localhost.
		# \param default
		#	Default prompt text to use instead of current state.
		def add_ipv4_option(self, option, section="", keywords=[], ip=None, default=None):
			assert ip is None or util.ip.validate_ipv4(ip), "ip must be a valid IPv4, or None"
			self.add_option(option=option, section=section, state=ip if ip else "127.0.0.1", keywords=keywords, callback=self.callback_ipv4, default=default)
		
		## Default mechanism for handling IPv6 address validation inputs.
		#
		# \param default
		#	If provided, will be the default value instead of the current state.
		def callback_ipv6(self, default=None):
			valid = False
			result = None
			while not valid:
				result = self.__raw_input('New IPv6 address for "%s"' % self.current["text"], self.current["state"] if default is None else default)
				valid = util.ip.validate_ipv6(result)
				if not valid:
					if _dsz_mode: dsz.ui.Echo("Invalid IPv6 address.", dsz.ERROR)
					else: print("Invalid IP address.")
			self.set_current_state(result)
		
		## Adds an IPv4 address stateful option with IP validation.
		#
		# \param option
		#	Option text
		# \param section
		#	See add_option()
		# \param keywords
		#	See add_option()
		# \param ip
		#	IP address to default option to. If not provided, defaults to IPv6 localhost.
		# \param default
		#	Default prompt text to use instead of current state.
		def add_ipv6_option(self, option, section="", keywords=[], ip=None, default=None):
			assert ip is None or util.ip.validate_ipv6(ip), "ip must be a valid IPv6, or None"
			self.add_option(option=option, section=section, state=ip if ip else "::1", keywords=keywords, callback=self.callback_ipv6, default=default)
		
		## Default mechanism for handling FRIEZERAMP addresses.
		#
		# \param default
		#	If provided, will be the default value instead of the current state.
		def callback_frz(self, default=None):
			valid = False
			result = None
			while not valid:
				result = self.__raw_input('New FRZ address for "%s"' % self.current["text"], self.current["state"] if default is None else default)
				valid = result and result[0] == 'z' and util.ip.validate_ipv4(result[1:])
				if not valid:
					if _dsz_mode: dsz.ui.Echo("Invalid IPv4 address.", dsz.ERROR)
					else: print("Invalid FRZ address.")
			self.set_current_state(result)
		
		## Adds an FRIEZERAMP address stateful option.
		#
		# FRIEZERAMP addresses are just IPv4 addresses with 'z' in front of them. Not
		# to be confused with actual IP addresses. These are often also called
		# CHIMNEYPOOL or CP addresses.
		#
		# \param option
		#	Option text
		# \param section
		#	See add_option()
		# \param keywords
		#	See add_option()
		# \param frz
		#	FRZ address to default option to. If not provided, defaults to one of two
		#	values: if inside DSZ, the local address. Outside of DSZ, assumes z0.0.0.1
		#	is still the local address.
		# \param default
		#	Default prompt text to use instead of current state.
		def add_frz_option(self, option, section="", keywords=[], frz=None, default=None):
			assert frz is None or (frz[0] == 'z' and util.ip.validate_ipv4(frz[1:])), "frz must be a valid FRZ address, or None"
			self.add_option(option=option, section=section, state=frz if frz else "z0.0.0.1", keywords=keywords, callback=self.callback_frz, default=default)

if __name__ == "__main__":
	test = Menu()
	test.add_option("Exit and do stuff")
	test.add_str_option("Log", section="Configuration", state=r"C:\Windows\Temp\log.log")
	test.add_hex_option("ID", section="Configuration", state=0x10002345)
	test.add_hex_option("ID", section="Configuration", state=0x100010002345)
	test.add_int_option("Loops", section="Advanced", state=3*3*3 * 3*3*3 * 3*3*3)
	if _util_ip_mode:
		test.add_ip_option("IP", section="Configuration", ip="1.2.3.4")
		test.add_ipv4_option("IPv4", section="Configuration", ip="9.6.3.0")
		test.add_ipv6_option("IPv6", section="Configuration", ip="1234:abcd::5%9")
		test.add_frz_option("FRZ", section="ADVANCED", frz="z7.7.7.7")
	print(test.execute(exiton=[1], default=1))
	