.phony: test
test:
	scripts/test-minikube

.phony: demo
demo:
	SKUPPER_DEMO=1 scripts/test-minikube

.phony: clean
clean:
	rm -rf scripts/__pycache__
	rm -f README.html

README.html: README.md
	pandoc -o $@ $<

.phony: update-%
update-%:
	curl -sfo scripts/$*.py "https://raw.githubusercontent.com/ssorj/$*/master/python/$*.py"
