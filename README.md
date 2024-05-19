# **AWS-K8S-Docker-Flask-Cloud-App**

## Goals

1. Python and How to create Monitoring Application in Python using Flask and psutil
2. How to run a Python App locally.
3. Learn Docker and How to containerize a Python application
    1. Creating Dockerfile
    2. Building DockerImage
    3. Running Docker Container
    4. Docker Commands
4. Create ECR repository using Python Boto3 and pushing Docker Image to ECR
5. Learn Kubernetes and Create EKS cluster and Nodegroups
6. Create Kubernetes Deployments and Services using Python!


## **Prerequisites** 

- [x]  AWS Account.
- [x]  Programmatic access and AWS configured with CLI.
- [x]  Python3 Installed.
- [x]  Docker and Kubectl installed.
- [x]  Code IDE (PyCharm)


## **Part 1: Deploying the Flask application locally**

### **Step 1: Clone the code**

Clone the code from the repository:

```
git clone <repository_url>
```

### **Step 2: Install dependencies**

The application uses the **`psutil`** and **`Flask`, Plotly, boto3** libraries. Install them using pip:

```
pip3 install -r requirements.txt
```

### **Step 3: Run the application**

To run the application, navigate to the root directory of the project and execute the following command:

```
python3 app.py
```

This will start the Flask server on **`localhost:5000`**. Navigate to [http://localhost:5000/](http://localhost:5000/) on your browser to access the application.

## **Part 2: Dockerizing the Flask application**

### **Step 1: Create a Dockerfile**

Create a **`Dockerfile`** in the root directory of the project with the following contents:

```
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

### **Step 2: Build the Docker image**

To build the Docker image, execute the following command:

```
 docker build -t <aws_repository>:latest <directory>/DockerFile
```

From: https://podman-desktop.io/docs/migrating-from-docker/emulating-docker-cli-with-podman

### **Step 3: Run the Docker container**

To run the Docker container, execute the following command:

```
docker run -p 5000:5000 <image_name>
```

This will start the Flask server in a Docker container on **`localhost:5000`**. Navigate to [http://localhost:5000/](http://localhost:5000/) on your browser to access the application.

## **Part 3: Pushing the Docker image to ECR**

### **Step 1: Create an ECR repository**

Create an ECR repository using Python:

```
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

### **Step 2: Push the Docker image to ECR**

Push the Docker image to ECR using the push commands on the console:

```
docker push <ecr_repo_uri>:<tag>
```

## **Part 4: Creating an EKS cluster and deploying the app using Python**

### **Step 1: Create an EKS cluster**

Create an EKS cluster and add node group

### **Step 2: Create a node group**

Create a node group in the EKS cluster.

### **Step 3: Create deployment and service**

```jsx
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
                        image="568373317874.dkr.ecr.us-east-1.amazonaws.com/my-cloud-native-repo:latest",
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

make sure to edit the name of the image on line 25 with your image Uri.

- Once you run this file by running “python3 eks.py” deployment and service will be created.
- Check by running following commands:

```eksctl get cluster```

Install eks

```jsx
kubectl get deployment -n default (check deployments)
kubectl get service -n default (check service)
kubectl get pods -n default (to check the pods)
```

Once your pod is up and running, run the port-forward to expose the service

```bash
kubectl port-forward service/<service_name> 5000:5000
```
![image](https://github.com/FarisDou/AWS-K8S-Docker-Flask-Cloud-App/assets/109401839/91bc52c4-cbe9-4593-8765-3a3884a12d5b)

 Creating a EKS Cluster
After pushing the docker image to ECR registry, we are good to go for creating a Kubernetes cluster in AWS EKS. Follow the following steps to create a EKS cluster on which we will host our Cloud-native-monitoring-application:

Go to the Search tab, type EKS and select Elastic Kubernetes services. It will open a new tab.

Select add Cluster and in the drop-down menu, click on Create. It will open the following page, add the details like Cluster name (cloud-native-cluster):



In the above image, you can see Cluster service role is set to myAmazonEKSRole, in your case, it will show noting. To create a role, search for IAM in the search tab and navigate to Roles tab.

In the Roles tab, Click on Create role and Select AWS services in the Trusted Entity type and Select EKS in service type, under use case, go for EKS-Cluster to create a custom policy like specified below:



After that click on next and give it a name (eg: myAmazonEKSRole) and go back to EKS page.

Now if you refresh the role drop down menu, you can see the role created by you. Select the role and keep the rest as default and click next.

In Specifying Networking settings, select your default VPC, subnets and security groups, make sure to remove any private subnets which you created and ensure that the security group you selected have port 5000 open.



After then leave the rest of the configurations as default and Review and create the Cluster.

The cluster will take up to 10-15 mins for creation. After the cluster is fully created, we will create Node group for our nodes.

💡 Creating Node Groups
Once the Cluster state is active, we will go to compute tab under our cloud-native-cluster and in the Node group section, Click on Add Node Group. It will Give you the following prompt in (enter details like node group and IAM role for the node).


In the above Image, you can see a Node IAM Role, just like before, you need to create an Eks role with the following permissions attached:


Remember to change the trusted relationship in the above image with the following Json, otherwise your role will not show up:

COPY

COPY
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
After creating the role, refresh the drop-down menu and select your role. Leave the rest and default and click on Next.

In Set compute and scaling configuration, select t2.micro as instance type and leave the rest as default.



Click on next, leave the default configuration as is it and Click on create the node group.

💡 Creating Kubernetes Deployments and Services
After initializing node group and cluster, we need to write the deployment and service file for the project to be deployed on cloud-native-cluster. Follow the next steps to create the yaml files:

In the project directory, create a file named eks.py and put the following content in it:


COPY

COPY
 #create deployment and service
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
In the above code, make sure to replace <Your-Image-URI> with the actual URI of the docker image you pushed on the ECR registry.

After creating that Open terminal and run the following command to connect your kubectl with the cloud-native-cluster:


COPY

COPY
 aws eks update-kubeconfig --name cloud-native-cluster
To apply the deployment and services, we created in the eks.py, run the file with the following command:


COPY

COPY
 python3 eks.py
After running the file, You can see the pods, deployments and services running into your cluster with the following command:


kubectl get all
It will give the following output:



To expose the service to the outside world, we need to use the following command:

kubectl port-forward service/my-flask-service 5000:5000

After exposing the service to the outside world, we can go to our localhost:5000 and you can see your application running which is actually running inside a Kubernetes cluster.
