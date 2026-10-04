# AWS K8S Docker Flask Cloud App

Build a Python system-monitoring app with Flask and psutil, containerize it with Docker, push the image to Amazon ECR, and run it on an Amazon EKS cluster using the Kubernetes Python client.

## What you'll use

- Python 3 with Flask, psutil, Plotly, and boto3 (see `requirements.txt`)
- Docker
- AWS ECR and EKS, the AWS CLI, `kubectl`, and `eksctl`
- The Kubernetes Python client
- A code editor (I used PyCharm)

## Prerequisites

- An AWS account with programmatic access, and the AWS CLI configured
- Python 3, Docker, and `kubectl` installed

## Steps

### Part 1: Run the Flask app locally

1. Clone the repository:

   ```bash
   git clone <repository_url>
   ```

2. Install the dependencies:

   ```bash
   pip3 install -r requirements.txt
   ```

3. From the project root, start the app:

   ```bash
   python3 app.py
   ```

4. Open http://localhost:5000/ in a browser.

   Expected result: a "System Monitoring" page with two gauges (0 to 100), CPU Utilization and Memory Utilization, each showing the current percentage (for example, CPU around 12 and memory around 71).

### Part 2: Containerize the app

5. Create a `Dockerfile` in the project root (this repo's copy is `DockerFile`):

   ```dockerfile
   # Use the official Python image as the base image
   FROM python:3.9-slim-buster

   # Set the working directory in the container
   WORKDIR /app

   # Copy the requirements file to the working directory
   COPY requirements.txt .

   RUN pip3 install --no-cache-dir -r requirements.txt

   # Copy the application code to the working directory
   COPY . .

   # Set the environment variables for the Flask app
   ENV FLASK_RUN_HOST=0.0.0.0

   # Expose the port on which the Flask app will run
   EXPOSE 5000

   # Start the Flask app when the container is run
   CMD ["flask", "run"]
   ```

6. Build the image:

   ```bash
   docker build -t <aws_repository>:latest <directory>/DockerFile
   ```

   If you use Podman instead of Docker, see [Emulating the Docker CLI with Podman](https://podman-desktop.io/docs/migrating-from-docker/emulating-docker-cli-with-podman).

7. Run the container:

   ```bash
   docker run -p 5000:5000 <image_name>
   ```

   Expected result: the same monitoring page loads at http://localhost:5000/, now served from the container.

### Part 3: Push the image to ECR

8. Create an ECR repository with boto3 (see `ecr.py`):

   ```python
   import boto3

   # Create an ECR client
   ecr_client = boto3.client('ecr')

   # Create a new ECR repository
   repository_name = 'my-ecr-repo'
   response = ecr_client.create_repository(repositoryName=repository_name)

   # Print the repository URI
   repository_uri = response['repository']['repositoryUri']
   print(repository_uri)
   ```

9. In the ECR console, open the repository, select View push commands, and run them. The last one pushes the image:

   ```bash
   docker push <ecr_repo_uri>:<tag>
   ```

### Part 4: Create the EKS cluster

10. In the AWS console, search for EKS and open Elastic Kubernetes Service.
11. Select Add cluster > Create and name the cluster `cloud-native-cluster`.
12. Create a cluster service role: open IAM > Roles > Create role, choose AWS service as the trusted entity, choose EKS as the service, and pick the EKS - Cluster use case. Name it (for example, `myAmazonEKSRole`).
13. Back on the EKS page, refresh the Cluster service role list, select your role, keep the other defaults, and select Next.
14. Under networking, select your default VPC, subnets, and security groups. Remove any private subnets you created, and make sure the security group allows port 5000.
15. Keep the remaining defaults, then review and create the cluster. Creation takes about 10 to 15 minutes.

### Part 5: Add a node group

16. When the cluster is Active, open its Compute tab and select Add node group. Enter a node group name and a node IAM role.
17. Create the node IAM role the same way as the cluster role, then edit its trust relationship to the JSON below, or the role will not appear in the list:

    ```json
    {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Principal": {
                    "Service": "ec2.amazonaws.com"
                },
                "Action": "sts:AssumeRole",
                "Condition": {}
            }
        ]
    }
    ```

18. Refresh the role list, select the role, keep the defaults, and select Next.
19. Under compute and scaling, choose `t2.micro` as the instance type, keep the defaults, and create the node group.

### Part 6: Deploy with Python

20. Create `eks.py` in the project directory. Replace `<Your-Image-URI>` with the ECR image URI you pushed, in the form `<your-aws-account-id>.dkr.ecr.us-east-1.amazonaws.com/my-cloud-native-repo:latest`:

    ```python
    # create deployment and service
    from kubernetes import client, config

    # Load Kubernetes configuration
    config.load_kube_config()

    # Create a Kubernetes API client
    api_client = client.ApiClient()

    # Define the deployment
    deployment = client.V1Deployment(
        metadata=client.V1ObjectMeta(name="my-flask-app"),
        spec=client.V1DeploymentSpec(
            replicas=1,
            selector=client.V1LabelSelector(
                match_labels={"app": "my-flask-app"}
            ),
            template=client.V1PodTemplateSpec(
                metadata=client.V1ObjectMeta(
                    labels={"app": "my-flask-app"}
                ),
                spec=client.V1PodSpec(
                    containers=[
                        client.V1Container(
                            name="my-flask-container",
                            image="<Your-Image-URI>",
                            ports=[client.V1ContainerPort(container_port=5000)]
                        )
                    ]
                )
            )
        )
    )

    # Create the deployment
    api_instance = client.AppsV1Api(api_client)
    api_instance.create_namespaced_deployment(
        namespace="default",
        body=deployment
    )

    # Define the service
    service = client.V1Service(
        metadata=client.V1ObjectMeta(name="my-flask-service"),
        spec=client.V1ServiceSpec(
            selector={"app": "my-flask-app"},
            ports=[client.V1ServicePort(port=5000)]
        )
    )

    # Create the service
    api_instance = client.CoreV1Api(api_client)
    api_instance.create_namespaced_service(
        namespace="default",
        body=service
    )
    ```

21. Point `kubectl` at the cluster:

    ```bash
    aws eks update-kubeconfig --name cloud-native-cluster
    ```

22. Create the deployment and service:

    ```bash
    python3 eks.py
    ```

23. Confirm the cluster, deployment, service, and pods:

    ```bash
    eksctl get cluster
    kubectl get deployment -n default
    kubectl get service -n default
    kubectl get pods -n default
    kubectl get all
    ```

24. When the pod is running, forward the service port:

    ```bash
    kubectl port-forward service/my-flask-service 5000:5000
    ```

    Expected result: http://localhost:5000/ shows the System Monitoring page with the CPU and memory gauges, now served from the pod in EKS.

## What I learned

- How to build a small monitoring dashboard with Flask, psutil, and Plotly.
- How to package a Python app as a Docker image and publish it to ECR with boto3.
- How EKS clusters and node groups depend on IAM roles and trust relationships.
- How to create Kubernetes deployments and services from Python instead of YAML.

## Next steps / cleanup

- Delete the node group, then the EKS cluster, and the ECR repository when you are done to avoid charges.
