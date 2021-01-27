.PHONY: test
test:
	python3 scripts/test-minikube

.PHONY: demo
demo:
	SKUPPER_DEMO=1 python3 scripts/test-minikube

.PHONY: clean
clean:
	rm -rf scripts/__pycache__
	rm -f README.html

README.html: README.md
	pandoc -o $@ $<
