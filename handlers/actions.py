'''
All rights reserved (c) 2016-2018 Brenda A. Bell.

This file is part of the PCGenerator (see
https://github.com/brendabell/knittingtools).

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program. If not, see <http://www.gnu.org/licenses/>.
'''

import cairosvg
import cgi
import os
import sys
import time
import traceback
import io

from modules.pcgenerator import PCGenerator
from modules.pcgenerator import calibrate

def pcgenerator_head(handler, logger):

	try:
		handler.send_response(200)
		handler.send_header('Content-type', 'text/html')
		handler.end_headers()

		return

	except Exception:
		wfile = io.TextIOWrapper(handler.wfile)

		exc_type, exc_value, exc_traceback = sys.exc_info()
		handler.log_error("%s", traceback.format_exception(exc_type, exc_value,exc_traceback))

		wfile.write(
			"<h1>Aw, snap! We seem to have a problem.</h1><p><b>")
		wfile.write(
			repr(traceback.format_exception(exc_type, exc_value,exc_traceback)))
		wfile.write(
			"</b><p>Please report this error via private message to "
			"<a href='http://www.ravelry.com/people/beebell'>beebell on Ravelry</a>. "
			"It will be helpful if you include the pattern you uploaded to help me "
			"diagnose the issue.")

		wfile.detach()

def pcgenerator_get(handler, logger):
	wfile = io.TextIOWrapper(handler.wfile)

	f = open("{}/../templates/{}".format(
		os.path.dirname(os.path.realpath(__file__)),
		"pcgenerator.html"))

	try:
		handler.send_response(200)
		handler.send_header('Content-type', 'text/html')
		handler.end_headers()
		wfile.write(f.read())

		return

	except Exception:
		exc_type, exc_value, exc_traceback = sys.exc_info()
		handler.log_error("%s", traceback.format_exception(exc_type, exc_value,exc_traceback))

		wfile.write(
			"<h1>Aw, snap! We seem to have a problem.</h1><p><b>")
		wfile.write(
			repr(traceback.format_exception(exc_type, exc_value,exc_traceback)))
		wfile.write(
			"</b><p>Please report this error via private message to "
			"<a href='http://www.ravelry.com/people/beebell'>beebell on Ravelry</a>. "
			"It will be helpful if you include the pattern you uploaded to help me "
			"diagnose the issue.")

	finally:
		f.close()
		wfile.detach()

def pcgenerator_post(handler, logger):
	wfile = io.TextIOWrapper(handler.wfile)

	try:
		ctype, pdict = cgi.parse_header(handler.headers.get('Content-Type'))
		if ctype == 'multipart/form-data':
			# For some reason parse_header outputs boundary as a string, but parse_multipart wants boundary as ascii-encoded bytes
			# Perhaps not a good solution.
			if isinstance(pdict["boundary"], str):
				pdict["boundary"] = pdict["boundary"].encode("ascii")

			query=cgi.parse_multipart(handler.rfile, pdict)

		calibrate_only = query.get('test', [''])[0] == 'test'
		is_blank = query.get('blank', [''])[0] == 'blank'
		is_solid_fill = query.get('fill', [''])[0] == 'fill'
		use_laser_colors = query.get('laser', [''])[0] == 'laser'
		polygon_circle = query.get('polygon', [''])[0] == 'polygon'

		result = None
		filename_template = None
		convert_to_png = False

		if calibrate_only:
			result = calibrate()
			filename_template = 'attachment; filename="calibrate-{}.{}"'
		else:
			upfilecontent = ['x']
			if not is_blank:
				upfilecontent = [a.decode() for a in query.get('upfile')]
				if len(upfilecontent[0]) > 4000:
					handler.send_response(302)
					handler.send_header('Content-type', 'text/html')
					handler.end_headers()
					wfile.write("Sorry. Your file cannot exceed 2500 bytes!")
					return
			machine_type = query.get('machine')
			vert_repeat = query.get('vert')
			convert_to_png = query.get('png', [''])[0] == 'png'

			generator = PCGenerator(
				handler,
				upfilecontent[0],
				machine_type[0],
				int(vert_repeat[0]),
				is_blank,
				is_solid_fill,
				use_laser_colors, 
				polygon_circle)
			result = generator.generate()
			filename_template = 'attachment; filename="punchcard-{}.{}"'

		handler.send_response(200)

		if convert_to_png:
			result = cairosvg.svg2png(bytestring=result)
			handler.send_header('Content-type', 'image/png')
			handler.send_header('Content-Disposition', filename_template.format(int(time.time()), "png"))
		else:
			handler.send_header('Content-type', 'image/svg+xml')
			handler.send_header('Content-Disposition', filename_template.format(int(time.time()), "svg"))

		handler.end_headers()
		wfile.write(result)

		return

	except (ValueError, RuntimeError, Exception) as e:
		exc_type, exc_value, exc_traceback = sys.exc_info()
		handler.log_error("%s", traceback.format_exception(exc_type, exc_value,exc_traceback))

		handler.send_response(400)
		handler.send_header('Content-type', 'text/html')
		handler.end_headers()
		wfile.write(
			"<h1>Aw, snap! We seem to have a problem.</h1><p>")
		for i in e.args:
			wfile.write(i)
		wfile.write(
			"<p><em>If you need assistance...</em><br><br>"
			"* Copy the entire contents of this page to the clipboard (Ctrl-A+Ctrl-C on Windows or Cmd-A+Cmd-C on Mac).<br>"
			"* Paste from the clibboard (Ctrl-V on Windows or Cmd-V on Mac) into a private message to"
			" <a href='http://www.ravelry.com/people/beebell'>beebell on Ravelry</a>.<br>"
			"* Please include the pattern you uploaded to help diagnose the issue.<br>")
		wfile.write("<p>Stack trace:<br><br>")
		stack = traceback.extract_stack()
		for i in stack:
			wfile.write(str(i))
			wfile.write('<br>')
	finally:
		wfile.detach()

def calculator_head(handler, logger):

	try:
		handler.send_response(200)
		handler.send_header('Content-type', 'text/html')
		handler.end_headers()

		return

	except Exception:
		wfile = io.TextIOWrapper(handler.wfile)

		exc_type, exc_value, exc_traceback = sys.exc_info()
		handler.log_error("%s", traceback.format_exception(exc_type, exc_value,exc_traceback))

		wfile.write(
			"<h1>Aw, snap! We seem to have a problem.</h1><p><b>")
		wfile.write(
			repr(traceback.format_exception(exc_type, exc_value,exc_traceback)))
		wfile.write(
			"</b><p>Please report this error via private message to "
			"<a href='http://www.ravelry.com/people/beebell'>beebell on Ravelry</a>. "
			"It will be helpful if you include the pattern you uploaded to help me "
			"diagnose the issue.")

		wfile.detach()

def calculator_get(handler, logger):
	wfile = io.TextIOWrapper(handler.wfile)

	f = open("{}/../templates/{}".format(
		os.path.dirname(os.path.realpath(__file__)),
		"calculator.html"))

	try:
		handler.send_response(200)
		handler.send_header('Content-type', 'text/html')
		handler.end_headers()
		wfile.write(f.read())

		return

	except Exception:
		exc_type, exc_value, exc_traceback = sys.exc_info()
		handler.log_error("%s", traceback.format_exception(exc_type, exc_value,exc_traceback))

		wfile.write(
			"<h1>Aw, snap! We seem to have a problem.</h1><p><b>")
		wfile.write(
			repr(traceback.format_exception(exc_type, exc_value,exc_traceback)))
		wfile.write(
			"</b><p>Please report this error via private message to "
			"<a href='http://www.ravelry.com/people/beebell'>beebell on Ravelry</a>. "
			"It will be helpful if you include the pattern you uploaded to help me "
			"diagnose the issue.")

	finally:
		f.close()
		wfile.detach()

def index_head(handler, logger):
	try:
		handler.send_response(200)
		handler.send_header('Content-type', 'text/html')
		handler.send_header('Content-Security-Policy', "frame-ancestors 'self' *.theotherbell.com")
		handler.end_headers()

		return

	except Exception:
		wfile = io.TextIOWrapper(handler.wfile)

		exc_type, exc_value, exc_traceback = sys.exc_info()
		handler.log_error("%s", traceback.format_exception(exc_type, exc_value,exc_traceback))

		wfile.write(
			"<h1>Aw, snap! We seem to have a problem.</h1><p><b>")
		wfile.write(
			repr(traceback.format_exception(exc_type, exc_value,exc_traceback)))
		wfile.write(
			"</b><p>Please report this error via private message to "
			"<a href='http://www.ravelry.com/people/beebell'>beebell on Ravelry</a>. "
			"It will be helpful if you include the pattern you uploaded to help me "
			"diagnose the issue.")

		wfile.detach()

def index_get(handler, logger):
	wfile = io.TextIOWrapper(handler.wfile)

	f = open("{}/../templates/{}".format(
		os.path.dirname(os.path.realpath(__file__)),
		"index.html"))

	try:
		handler.send_response(200)
		handler.send_header('Content-type', 'text/html')
		handler.send_header('Content-Security-Policy', "frame-ancestors 'self' *.theotherbell.com")
		handler.end_headers()
		wfile.write(f.read())

		return

	except Exception:
		exc_type, exc_value, exc_traceback = sys.exc_info()
		handler.log_error("%s", traceback.format_exception(exc_type, exc_value,exc_traceback))

		wfile.write(
			"<h1>Aw, snap! We seem to have a problem.</h1><p><b>")
		wfile.write(
			repr(traceback.format_exception(exc_type, exc_value,exc_traceback)))
		wfile.write(
			"</b><p>Please report this error via private message to "
			"<a href='http://www.ravelry.com/people/beebell'>beebell on Ravelry</a>. "
			"It will be helpful if you include the pattern you uploaded to help me "
			"diagnose the issue.")

	finally:
		f.close()
		wfile.detach()
