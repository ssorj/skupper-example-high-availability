from skewer import *

def run_test(west_kubeconfig, east_kubeconfig):
    # XXX
    ENV["SKUPPER_PROXY_IMAGE"] = "quay.io/skupper/proxy:latest"
    ENV["SKUPPER_CONTROLLER_IMAGE"] = "quay.io/ernieallen/controller:latest"
    # End XXX

    connection_token = make_temp_file()

    with working_env(KUBECONFIG=west_kubeconfig):
        call("kubectl create namespace west")
        call("kubectl config set-context --current --namespace west")
        call("kubectl create deployment hello-world-frontend --image quay.io/skupper/hello-world-frontend")
        call("kubectl create deployment hello-world-backend --image quay.io/skupper/hello-world-backend")

        call("skupper init")

    with working_env(KUBECONFIG=east_kubeconfig):
        call("kubectl create namespace east")
        call("kubectl config set-context --current --namespace east")
        call("kubectl create deployment hello-world-frontend --image quay.io/skupper/hello-world-frontend")
        call("kubectl create deployment hello-world-backend --image quay.io/skupper/hello-world-backend")

        call("skupper init --edge")

    with working_env(KUBECONFIG=west_kubeconfig):
        wait_for_resource("deployment", "skupper-proxy-controller")
        wait_for_resource("deployment", "skupper-router")
        wait_for_resource("deployment", "hello-world-frontend")
        wait_for_resource("deployment", "hello-world-backend")

        call("skupper status")
        call(f"skupper connection-token {connection_token}")

    with working_env(KUBECONFIG=east_kubeconfig):
        wait_for_resource("deployment", "skupper-proxy-controller")
        wait_for_resource("deployment", "skupper-router")
        wait_for_resource("deployment", "hello-world-frontend")
        wait_for_resource("deployment", "hello-world-backend")

        call("skupper status")
        call(f"skupper connect {connection_token} --connection-name east-west")

        wait_for_connection("east-west")

        call("skupper expose deployment hello-world-frontend --port 8080 --protocol http")
        call("skupper expose deployment hello-world-backend --port 8080 --protocol http")

        call("skupper list-exposed") # XXX

    with working_env(KUBECONFIG=west_kubeconfig):
        call("skupper expose deployment hello-world-frontend --port 8080 --protocol http")
        call("skupper expose deployment hello-world-backend --port 8080 --protocol http")

        call("skupper list-exposed") # XXX

        wait_for_resource("service", "hello-world-backend")
        wait_for_resource("deployment", "hello-world-backend-proxy")

        call("kubectl apply -f ingress.yaml")

        frontend_ip = get_ingress_ip("ingress", "hello-world-frontend")
        frontend_url = f"http://{frontend_ip}/"

    try:
        for i in range(10):
            call(f"curl -f {frontend_url}")
    except:
        with working_env(KUBECONFIG=east_kubeconfig):
            call("kubectl logs deployment/hello-world-frontend")
            call("kubectl logs deployment/hello-world-frontend-proxy")
            call("kubectl logs deployment/hello-world-backend")
            call("kubectl logs deployment/hello-world-backend-proxy")

        with working_env(KUBECONFIG=west_kubeconfig):
            call("kubectl logs deployment/hello-world-frontend")
            call("kubectl logs deployment/hello-world-frontend-proxy")
            call("kubectl logs deployment/hello-world-backend")
            call("kubectl logs deployment/hello-world-backend-proxy")

        raise

    if "SKUPPER_DEMO" in ENV:
        with working_env(KUBECONFIG=west_kubeconfig):
            console_ip = get_ingress_ip("service", "skupper-controller")
            console_url = f"http://{console_ip}:8080/"
            password_data = call_for_stdout("kubectl get secret skupper-console-users -o jsonpath='{.data.admin}'")
            password = base64_decode(password_data).decode("ascii")

        print()
        print("Demo time!")
        print()
        print(f"West kubeconfig: {west_kubeconfig}")
        print(f"East kubeconfig: {east_kubeconfig}")
        print(f"Frontend URL: {frontend_url}")
        print(f"Console URL: {console_url}")
        print("User: admin")
        print(f"Password: {password}")
        print()

        while input("Are you done (yes)? ") != "yes":
            pass

    with working_env(KUBECONFIG=east_kubeconfig):
        call("skupper delete")
        call("kubectl delete service/hello-world-backend")
        call("kubectl delete deployment/hello-world-backend")

    with working_env(KUBECONFIG=west_kubeconfig):
        call("skupper delete")
        call("kubectl delete deployment/hello-world-frontend")
