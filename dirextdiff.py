#!/usr/bin/env python3


import subprocess
import argparse
import re
import tempfile
import os
import shutil

def dirextdiff(a, b, command):
	"""
	diff the specified files or directories using an external command.

	Arguments:
	a -- the base file or directory
	b -- the changed file or directory
	command -- a list of command arguments; in each argument, the keys
	{a} and {b} will be interpolated using str.format
	"""
	try:
		diff_out = subprocess.check_output(('diff', '-r', '-q', a, b),
		                                   universal_newlines=True)
	except subprocess.CalledProcessError as e:
		if e.returncode == 1:
			diff_out = e.output
		else:
			raise
	changed_files = []
	for line in diff_out.split('\n'):
		m = re.match('Files (.+) and (.+) differ', line)
		if m:
			changed_files.append((os.path.abspath(m.group(1)),
			                      os.path.abspath(m.group(2)),
			                      os.path.relpath(m.group(1), a),
			                      os.path.relpath(m.group(2), b)))
		else:
			print(line)

	with tempfile.TemporaryDirectory(prefix='dirextdiff') as tmp:
		atmp = os.path.join(tmp, 'a')
		btmp = os.path.join(tmp, 'b')
		os.mkdir(atmp)
		os.mkdir(btmp)
		for (afile, bfile, arel, brel) in changed_files:
			os.makedirs(os.path.dirname(os.path.join(atmp, arel)),
			            exist_ok=True)
			os.makedirs(os.path.dirname(os.path.join(btmp, brel)),
			            exist_ok=True)
			shutil.copy(afile, os.path.join(atmp, arel))
			shutil.copy(bfile, os.path.join(btmp, brel))

		subprocess.call([x.format(a=atmp, b=btmp) for x in command])

		for (afile, bfile, arel, brel) in changed_files:
			shutil.copy(os.path.join(atmp, arel), afile)
			shutil.copy(os.path.join(btmp, brel), bfile)

programs = {'diff': ('diff', '-u', '{a}', '{b}'),
            'ediff': ('emacs', '--eval', '(ediff-directories "{a}" "{b}" "")'),
            'colordiff': ('colordiff', '-u', '{a}', '{b}')}

def main():
	argparser = argparse.ArgumentParser()
	argparser.add_argument('a', help='the base file or directory')
	argparser.add_argument('b', help='the changed file or directory')
	argparser.add_argument('program', nargs='?', choices=programs.keys(),
	                       help=('the external program to use (default diff)'))
	argparser.add_argument('-c', '--command', nargs=argparse.REMAINDER,
	                       help=('command arguments; in each argument, the '
	                             'keys {a} and {b} will be interpolated using '
	                             'str.format'))
	args = argparser.parse_args()

	dirextdiff(args.a, args.b,
	           args.command if args.command else programs[args.program])
if __name__ == '__main__':
	main()
