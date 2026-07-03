# Training Operator for OpenShift

This project adds a `Training` Custom Resource to OpenShift.
A Python controller (built with **kopf**) watches the CRs and writes them to a SQLite database.
A **Flask** web app reads that database and shows a live Training Calendar using Server-Sent Events (SSE).

---

## Architecture

```
oc apply -f training.yaml
        |
        v
[Training CR]  ----watches----> [Training Controller (kopf)]
                                         |
                                         v
                                  [SQLite DB on PVC]
                                         |
                                         v
                             [Flask Web App / SSE stream]
                                         |
                                         v
                              [Browser - live calendar]
```

Both the controller and the webapp share the same PVC mounted at `/data/trainings.db`.
The webapp polls the DB every 2 seconds and pushes changes to all connected browsers via SSE.

---

## Step 1 - Apply the CRD

```bash
oc apply -f crd/training-crd.yaml

# Verify
oc get crd trainings.tektutor.org
oc describe crd trainings.tektutor.org
```

---

## Step 2 - Build and push images

```bash
# Controller
cd controller/
podman build -t quay.io/tektutor/training-controller:latest .
podman push quay.io/tektutor/training-controller:latest

# Webapp
cd ../webapp/
podman build -t quay.io/tektutor/training-webapp:latest .
podman push quay.io/tektutor/training-webapp:latest
```

Replace `quay.io/tektutor` with your actual registry namespace.
Update the `image:` fields in `deploy/controller-deployment.yaml` and `deploy/webapp-deployment.yaml` accordingly.

---

## Step 3 - Deploy to OpenShift

```bash
# RBAC
oc apply -f deploy/rbac.yaml

# Shared database volume
oc apply -f deploy/pvc.yaml

# Controller
oc apply -f deploy/controller-deployment.yaml

# Web app + Service + Route
oc apply -f deploy/webapp-deployment.yaml

# Verify pods are running
oc get pods -n jegan -l app=training-controller
oc get pods -n jegan -l app=training-webapp
```

---

## Step 4 - Get the web app URL

```bash
oc get route training-calendar -n jegan
```

Open the URL in your browser. The page connects via SSE and updates in real time.

---

## Step 5 - Create Training CRs

```bash
# Apply samples
oc apply -f crd/sample-trainings.yaml

# Or create one manually
oc apply -f - <<EOF
apiVersion: tektutor.org/v1
kind: Training
metadata:
  name: ansible-automation
  namespace: jegan
spec:
  trainingName: "Ansible Automation"
  duration: 2
  fromDate: "2026-08-04"
  toDate:   "2026-08-05"
  mode: Classroom
EOF
```

Watch it appear on the calendar within 2-3 seconds.

---

## Useful commands

```bash
# List all trainings with custom columns
oc get trainings -n jegan

# Describe a specific training
oc describe training openshift-fundamentals -n jegan

# Watch controller logs
oc logs -f deploy/training-controller -n jegan

# Update a training (edit the CR - controller picks up the change)
oc edit training openshift-fundamentals -n jegan

# Delete a training (removed from calendar immediately)
oc delete training openshift-fundamentals -n jegan
```

---

## How SSE works here

1. Browser opens `/stream` - Flask assigns it a `queue.Queue`.
2. A background thread polls the DB every 2 seconds.
3. When the data changes, it puts the new JSON into every connected client's queue.
4. Each browser receives the event and re-renders the table without a page reload.
5. New rows flash green to draw attention.

---

## Notes for local testing (without OpenShift)

```bash
pip install kopf kubernetes flask gunicorn

# Run controller (needs kubeconfig)
DB_PATH=/tmp/trainings.db kopf run controller/controller.py

# Run webapp in another terminal
DB_PATH=/tmp/trainings.db python webapp/app.py
```

Then visit http://localhost:8080 and apply Training CRs via `kubectl` or `oc`.
