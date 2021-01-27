from skewer import *

def run_test(west_kubeconfig, east_kubeconfig):
    # ENV["SKUPPER_PROXY_IMAGE"] = "quay.io/skupper/proxy:latest"
    # ENV["SKUPPER_CONTROLLER_IMAGE"] = "quay.io/ernieallen/controller:latest"

    connection_token = make_temp_file()

    with working_env(KUBECONFIG=west_kubeconfig):
        run("kubectl create namespace west")
        run("kubectl config set-context --current --namespace west")
        run("kubectl create deployment hello-world-frontend --image quay.io/skupper/hello-world-frontend")
        run("kubectl create deployment hello-world-backend --image quay.io/skupper/hello-world-backend")

        run("skupper init")

    with working_env(KUBECONFIG=east_kubeconfig):
        run("kubectl create namespace east")
        run("kubectl config set-context --current --namespace east")
        run("kubectl create deployment hello-world-frontend --image quay.io/skupper/hello-world-frontend")
        run("kubectl create deployment hello-world-backend --image quay.io/skupper/hello-world-backend")

        run("skupper init --cluster-local")

    with working_env(KUBECONFIG=west_kubeconfig):
        await_resource("deployment", "skupper-service-controller")
        await_resource("deployment", "skupper-router")
        await_resource("deployment", "hello-world-frontend")
        await_resource("deployment", "hello-world-backend")

        run("skupper status")
        run(f"skupper connection-token {connection_token}")

    with working_env(KUBECONFIG=east_kubeconfig):
        await_resource("deployment", "skupper-service-controller")
        await_resource("deployment", "skupper-router")
        await_resource("deployment", "hello-world-frontend")
        await_resource("deployment", "hello-world-backend")

        run("skupper status")
        run(f"skupper connect {connection_token} --connection-name east-west")

        await_connection("east-west")

        run("skupper expose deployment hello-world-frontend --port 8080 --protocol http")
        run("skupper expose deployment hello-world-backend --port 8080 --protocol http")

        run("skupper list-exposed") # XXX

    with working_env(KUBECONFIG=west_kubeconfig):
        run("skupper expose deployment hello-world-frontend --port 8080 --protocol http")
        run("skupper expose deployment hello-world-backend --port 8080 --protocol http")

        run("skupper list-exposed") # XXX

        await_resource("service", "hello-world-backend")

        run("kubectl apply -f ingress.yaml")

        frontend_ip = get_ingress_ip("ingress", "hello-world-frontend")
        frontend_url = f"http://{frontend_ip}/"

    # XXX Replace this with a wait operation when it's available
    sleep(30)

    try:
        for i in range(10):
            run(f"curl -f {frontend_url}")
    except:
        with working_env(KUBECONFIG=east_kubeconfig):
            run("kubectl logs deployment/hello-world-frontend")
            run("kubectl logs deployment/hello-world-backend")

        with working_env(KUBECONFIG=west_kubeconfig):
            run("kubectl logs deployment/hello-world-frontend")
            run("kubectl logs deployment/hello-world-backend")

        raise

    if "SKUPPER_DEMO" in ENV:
        with working_env(KUBECONFIG=west_kubeconfig):
            console_ip = get_ingress_ip("service", "skupper-controller")
            console_url = f"http://{console_ip}:8080/"
            password_data = call("kubectl get secret skupper-console-users -o jsonpath='{.data.admin}'")
            password = base64_decode(password_data).decode("ascii")

        print()
        print("Demo time!")
        print()
        print(f"West kubeconfig: export KUBECONFIG={west_kubeconfig}")
        print(f"East kubeconfig: export KUBECONFIG={east_kubeconfig}")
        print(f"Frontend URL: {frontend_url}")
        print(f"Console URL: {console_url}")
        print("User: admin")
        print(f"Password: {password}")
        print()

        while input("Are you done (yes)? ") != "yes":
            pass

    with working_env(KUBECONFIG=east_kubeconfig):
        run("skupper delete")
        run("kubectl delete service/hello-world-backend")
        run("kubectl delete deployment/hello-world-backend")

    with working_env(KUBECONFIG=west_kubeconfig):
        run("skupper delete")
        run("kubectl delete deployment/hello-world-frontend")
