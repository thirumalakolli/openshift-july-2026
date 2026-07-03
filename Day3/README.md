# Day 3

## Info - You can find Red Hat Base images here
<pre>
https://catalog.redhat.com/en/software/containers/explore
</pre>

## Info - You can find other Red Hat Openshift compatible images here
<pre>
https://catalog.redhat.com/en/search?searchType=Containers
</pre>  

## Info - What happens internally in Openshift when we deploy an application
```
oc project jegan-project
oc create deploy nginx --image=image-registry.openshift-image-registry.svc:5000/openshift/bitnami-nginx:1.26 --replicas=3
```

Note
<pre>
- oc client tool makes a REST call to API Server requesting the API Server to create a deployment
- Once API Server receives the request from oc client, it creates a Deployment database entry in etcd database
- API Server then sends broadcasting event saying new Deployment created along with deployment details
- Deployment Controller receives this event, it then makes a REST call to API Server requesting it to create a ReplicaSet for the nginx deployment
- API Server creates a ReplicaSet db entry(new record) in the etcd database
- API Server sends a broadcast event saying new ReplicaSet created
- ReplicaSet Controller receives the event, it then makes a REST call to API Server requesting it to create 3 Pods
- API Server create 3 Pod records in the etcd database
- API Server sends broadcast event for each new Pod created in the etcd database
- Scheduler receives the event, it then identifies a healthy node where the new Pod can be deployed
- Scheduler makes a REST call to API Server to send it scheduling recommendataion. This will be done for each Pod.
- API Server receives the scheduling recommendations from Scheduler, it then retrieves the Pod record from etcd and updates it status as Scheduled to so and so node
- API Server sends a broadcasting event saying Pod1 scheduled to Worker01 node, this happens for each Pod.
- Kubelet Container Agent that runs on Worker01 node receives the event, it then pull the container image, creates and starts the container on Worker01
- Kubelet monitors the status of the Container created for Pod1, and it periodically updates the status back to API Server in a heart-beat fashion
- API Server receives these updates, retrieves the Pod database entry from etcd and updates the Pod status
</pre>
![Openshift](openshift-internals.png)

## Lab - Deploying a stateless application in declarative style
```
# Delete your existing project
oc delete project jegan

# Create a new project
oc new-project jegan

# Generate the declarative manifest file to deploy nginx
oc create deploy nginx --image=image-registry.openshift-image-registry.svc:5000/openshift/bitnami-nginx:1.26 --replicas=3 --dry-run=client -o yaml

# Redirect the output shown to a yaml file
oc create deploy nginx --image=image-registry.openshift-image-registry.svc:5000/openshift/bitnami-nginx:1.26 --replicas=3 --dry-run=client -o yaml > nginx-deploy.yml

# Deploy the nginx in declarative fashion
oc create -f nginx-deploy.yml --save-config

# In the template section of the nginx-deploy.yml add additional labels and apply
oc apply -f nginx-deploy.yml

# List the deploy,replicaset and pods
oc get deploy,rs,po

## Delete the deployment declaratively
oc delete -f nginx-deploy.yml
oc get deploy,rs,po
```

## Lab - Creating a ClusterIP Internal Service in declarative style
Create a pod.yml with code below
<pre>
apiVersion: v1
kind: Pod
metadata:
  labels:
    app: test
  name: test-pod
spec:
  containers:
  - image: image-registry.openshift-image-registry.svc:5000/openshift/hello:latest
    imagePullPolicy: IfNotPresent
    name: test  
</pre>

Create the test pod
```
oc project jegan-project
oc apply -f pod.yml
oc get pods
```

Let's create the nginx deployment in declarative style
```
oc create deploy nginx --image=image-registry.openshift-image-registry.svc:5000/openshift/bitnami-nginx:1.26 --replicas=3 --dry-run=client -o yaml
oc create deploy nginx --image=image-registry.openshift-image-registry.svc:5000/openshift/bitnami-nginx:1.26 --replicas=3 --dry-run=client -o yaml > nginx-deploy.yml
oc apply -f nginx-deploy.yml
```

Let's create the ClusterIP Internal service declaratively
```
oc expose deploy/nginx --type=ClusterIP --port=8080 --dry-run=client -o yaml
oc expose deploy/nginx --type=ClusterIP --port=8080 --dry-run=client -o yaml > nginx-clusterip-svc.yml
oc apply -f nginx-clusterip-svc.yml
oc get svc
oc describe svc/nginx
```

Let's test the clusterip internal service using the test pod we created
```
oc rsh pod/test-pod
curl http://nginx:8080 # Service discovery - accessing service by its name
curl http://nginx.jegan-project.svc.cluster.local:8080 # Recommended compared to previous command
curl http://172.30.240.164:8080
```

## Lab - Creating an external NodePort service in declarative style
```
oc project jegan-project

# Delete existing clusterip service before creating nodeport service
oc delete -f nginx-clusterip-svc.yml

oc expose deploy/nginx --type=NodePort --port=8080 --dry-run=client -o yaml
oc expose deploy/nginx --type=NodePort --port=8080 --dry-run=client -o yaml > nginx-nodeport-svc.yml
oc apply -f nginx-nodeport-svc.yml
oc get svc
oc describe svc/nginx # Get the NodePort from this command and substitute below

oc get nodes -o wide
```

Let's test the nodeport external service ( don't need to run this inside pod shell )
```
curl http://192.168.100.11:31728 # Master1 IP
curl http://192.168.100.12:31728 # Master2 IP
curl http://192.168.100.13:31728 # Master3 IP
curl http://192.168.100.21:31728 # Worker1 IP
curl http://192.168.100.22:31728 # Worker2 IP
curl http://192.168.100.23:31728 # Worker3 IP

curl http://master01.ocp4.palmeto.org:31728
curl http://master02.ocp4.palmeto.org:31728
curl http://master03.ocp4.palmeto.org:31728
curl http://worker01.ocp4.palmeto.org:31728
curl http://worker02.ocp4.palmeto.org:31728
curl http://worker03.ocp4.palmeto.org:31728
```

## Lab - LoadBalancer service in declarative style
```
oc project jegan-project

# Delete exisitng node port service
oc delete -f nginx-nodeport-svc.yml

# Create the LoadBalancer service in declarative style
oc expose deploy/nginx --type=LoadBalancer --port=8080 --dry-run=client -o yaml > nginx-lb-svc.yml
oc apply -f nginx-lb-svc.yml

oc get svc
oc describe svc/nginx # You need to find your loadbalancer service ip and use it below in the curl 

# Testing the loadbalancer service
curl http://192.168.100.50:8080
```

## Lab - Rolling update ( upgrading nginx from version 1.26 to 1.27 and later to 1.28 )

Let's delete your exisitng project
```
oc delete project jegan-project
```

Let's create new project
```
oc new-project jegan-project
oc create deploy nginx --image=image-registry.openshift-image-registry.svc:5000/openshift/bitnami-nginx:1.26 --replicas=3 --dry-run=client -o yaml > nginx-deploy.yml
oc apply -f nginx-deploy.yml

oc get pods -o yaml | grep image
```

## Lab - Create an external route for nginx service
```
# Delete existing project
oc delete project jegan-project

# Deploy nginx
oc new-project jegan-project
oc create deploy nginx --image=image-registry.openshift-image-registry.svc:5000/openshift/bitnami-nginx:1.26 --replicas=3 --dry-run=client -o yaml > nginx-deploy.yml
oc apply -f nginx-deploy.yml

# Create clusterip internal service for nginx deployment
oc expose deploy/nginx --port=8080 --dry-run=client -o yaml > nginx-internal-svc.yml
oc apply -f nginx-internal-svc.yml

# Create an external route for internal service
oc expose svc/nginx
oc get route
curl http://nginx-jegan-project.apps.ocp4.palmeto.org
```

## Info - ConfigMap
<pre>
- is a map that stores data in key/value format
- instead of hard-coding, we store certain details like NFS Server IP, NFS Share Path, etc in the config map
- generally used for storing this like
  - JDK_HOME, MAVEN_HOME, LOG_PATH, etc.,
- deployment can retrieve the details from the ConfigMap and use it
- this is good for non-sensitive data
</pre>

## Info - Secrets
<pre>
- is also map that stores data in key/value format
- it is used to store any sensitive confidential data like login credentials, certificates, etc.,
</pre>

## Info - Persistent Volume (PV)
<pre>
- is an external disk/storage 
- this type of storage can come from NFS,NAS,AWS S3, etc.,
- this is always created on the cluster-wide and accessible to all projects in the cluster
- this can be provisioned manually by Administrators or can be provisioned on demand dynamically if there is a StorageClass
- Generally in case of NFS 
  - we need to mention NFS Server IP/Hostname
  - Disk size required in MiB/GiB/TiB
  - StorageClass ( Optional )
  - Access 
    - ReadWriteOnce
    - ReadWriteMany
</pre>

## Info - Persistent Volume Claim (PVC)
<pre>
- a application that runs in a Pod will have to request for external storage in Openshift/Kubernetes by defining
  its requirement in a Persistent Volume Claim
- generally created by non-admin, usually the dev team and it is created in the project scope
- If the Storage Controller is able to locate a matching Peristent Volume, then it let the PVC go and claim and use the PV
- the applicaiton Pod that needs the store will refer the PVC name in the deployment, and it can request the external store
  to be mounted in its preferred mount point within the Pod
</pre>

## Lab - Deploy wordpress and mariadb multi-pod application
```
# Clone the TekTutor Training repository if you haven't done it already on the lab machine
cd ~
git clone https://github.com/tektutor/openshift-july-2026.git
cd openshift-july-2026
cd Day3/wordpress-with-configmaps-and-secrets
# Ensure name 'jegan' is replaced with yours in all the yml file
# Ensure /var/nfs/jegan/wordpress, /var/nfs/jegan/mysql is replaced with your linux user ( update mysql-pv.yml mysql-pvc.yml wordpress-pv.yml wordpress-pvc.yml )
# Ensure NFS IP is updated to 192.168.10.201 in case you are working in server 2
# Ensure mysql-deploy.yml update the pvc name with the one that you created
# Ensure wordpress-deploy.yml update the pvc name with the one that you created

oc delete project jegan-project
oc new-project jegan-project
./deploy.sh

oc get pods

# Then switch to Openshift webconsole Topolgy and click on the wordpress route(up arrow) to see the blog
```

## Demo - Installing Helm package manager
```
sudo su -
curl -fsSL -o get_helm.sh https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-4
chmod 700 get_helm.sh
./get_helm.sh
```

## Info - Helm Overview
<pre>
- helm is a package manager for Kubernetes & Openshift
- helm is a Kubernetes/Openshift aware tool, hence it knows how to find the dependency and figure out the sequence in which
  K8s/Openshift resources must be created
- the helm packaged application is called Helm chart
- Openshift comes with pre-integrated Helm support
- However, we can deploy application from Helm Charts from command-line as well as from the Openshift webconsole
</pre>

## Lab -  Packaging wordpress multi-pod application as Helm chart and deploying into Openshift
```
cd ~
mkdir -p wordpress-helm-chart
cd wordpress-helm-chart

helm version
helm create wordpress
tree
cd wordpress/templates
rm *
rm -rf tests
cp ~/openshift-july-2026/Day3/wordpress-helm-chart/manifest-scripts/*.yml .
cd ..
cp ~/openshift-july-2026/Day3/wordpress-helm-chart/values.yaml .
cd ..
tree wordpress

helm package wordpress
helm install worpress wordpress-0.1.0.tgz
oc get pods

# Switch to your openshift webconsole topology in your project

# Once you are done you may undeploy
helm list
helm uninstall wordpress 
```
