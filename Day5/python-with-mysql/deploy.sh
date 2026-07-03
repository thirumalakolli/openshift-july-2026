oc apply -f mysql-secret.yml
oc apply -f mysql-pv.yml
oc apply -f mysql-pvc.yml
oc apply -f mysql-deploy.yml
oc apply -f mysql-svc.yml

oc new-app --name=flask-app https://github.com/tektutor/openshift-1317oct-2025.git --context-dir=Day4/python-with-mysql --strategy=docker

oc expose svc/flask-app
