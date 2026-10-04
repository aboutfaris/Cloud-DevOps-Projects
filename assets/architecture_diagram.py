#!/usr/bin/env python3
"""Cloud DevOps Set: high-level architecture diagram.

Adapted from the reference implementation for AWS architecture diagrams
(.kiro/steering/aws-architecture-diagram-style.md). Deviations for this repo:
  - No company branding or footer.
  - The set spans two clouds, so there are two lanes, each with its own boundary:
    01 AWS (official AWS icons) and 02 Microsoft Azure (official Azure icons).
  - Workstation tools use their vendor icons (Flask, Docker, Python, Terraform).

Run:  /tmp/diagram_venv/bin/python architecture_diagram.py <out-prefix>
It writes <out-prefix>.svg and <out-prefix>.png (rendered at 2x) and must print
"layout problems: none".
"""
import base64
import os
import subprocess
import sys

import diagrams

R = os.path.join(os.path.dirname(os.path.dirname(diagrams.__file__)), "resources")
OUT = sys.argv[1] if len(sys.argv) > 1 else "/tmp/arch"
OUT_SVG, OUT_PNG = OUT + ".svg", OUT + ".png"

# ---------------- style: owner-approved, keep as is ----------------
FONT = "Helvetica Neue, Helvetica, Arial, sans-serif"
INK, TEXT2, LINE, GROUP, BADGE, ORANGE, RULE, ACCENT = (
    "#232F3E", "#545B64", "#3F4752", "#7D8998", "#146EB4", "#FF9900", "#E3E6EA", "#8C4FFF")
ICON, HALF = 52, 26
KINDS = {  # stroke, width, dash, arrowhead marker, legend label
    "service": (LINE, 1.6, None, "ah", "Flow inside a cloud"),
    "external": (LINE, 1.6, "6 5", "ah", "Command or traffic from your workstation"),
    "business": (ACCENT, 2.2, None, "ahb", "Business flow"),
}

# ---------------- canvas text ----------------
W, H = 1600, 1270
TITLE = "Cloud DevOps Set | Architecture"
SUBTITLE = ("Two independent follow-along projects: 01 runs a Flask monitoring app on "
            "Amazon EKS, 02 deploys an Azure static website with Terraform.")

out, icons, SEGS, BADGES, GRECTS = [], [], [], [], []
N, BOX, USED = {}, {}, set()


def add(s):
    out.append(s)


def esc(t):
    return t.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def est_w(s, size):
    return len(s) * size * 0.53


def text(x, y, s, size=13, weight=400, color=INK, anchor="middle", halo=False):
    h = (' stroke="#FFFFFF" stroke-width="5" stroke-linejoin="round" paint-order="stroke"'
         if halo else "")
    add(f'<text x="{x}" y="{y}" font-family="{FONT}" font-size="{size}" '
        f'font-weight="{weight}" fill="{color}" text-anchor="{anchor}"{h}>{esc(s)}</text>')


_cache = {}


def data(rel):
    if rel not in _cache:
        with open(os.path.join(R, rel), "rb") as fh:
            _cache[rel] = "data:image/png;base64," + base64.b64encode(fh.read()).decode()
    return _cache[rel]


def node(key, rel, cx, cy, l1, l2=None):
    """Register an icon at slot (cx, cy) with a service name and an optional role line."""
    assert key not in N, key
    N[key] = (cx, cy, 2 if l2 else 1)
    icons.append((rel, cx, cy, l1, l2))
    w = max(ICON, est_w(l1, 13), est_w(l2 or "", 12))
    BOX[key] = (cx - w / 2, cy - HALF, cx + w / 2, cy + HALF + (36 if l2 else 21))


def draw_nodes():
    for rel, cx, cy, l1, l2 in icons:
        add(f'<image x="{cx-HALF}" y="{cy-HALF}" width="{ICON}" height="{ICON}" '
            f'xlink:href="{data(rel)}"/>')
        text(cx, cy + HALF + 17, l1, 13, 400, INK)
        if l2:
            text(cx, cy + HALF + 32, l2, 12, 400, TEXT2)


def port(key, side, gap=5):
    """Connection point: l, r, t (top edge of icon), b (below the label block)."""
    cx, cy, n = N[key]
    return {"l": (cx - HALF - gap, cy), "r": (cx + HALF + gap, cy),
            "t": (cx, cy - HALF - gap),
            "b": (cx, cy + HALF + (36 if n == 2 else 21) + gap)}[side]


def path(pts, a, b, kind="service"):
    color, width, dash, marker, _ = KINDS[kind]
    USED.add(kind)
    for p, q in zip(pts, pts[1:]):
        assert p[0] == q[0] or p[1] == q[1], ("diagonal segment", a, b, p, q)
        SEGS.append((p, q, a, b))
    d = "M " + " L ".join(f"{x},{y}" for x, y in pts)
    da = f' stroke-dasharray="{dash}"' if dash else ""
    add(f'<path d="{d}" fill="none" stroke="{color}" stroke-width="{width}"{da} '
        f'marker-end="url(#{marker})"/>')


def link(a, sa, b, sb, kind="service", via=None):
    """Connect two nodes. via = elbow points; every segment must be horizontal or vertical."""
    path([port(a, sa)] + (via or []) + [port(b, sb)], a, b, kind)


def badge(cx, cy, n, record=True):
    if record:
        BADGES.append((cx, cy, n))
    add(f'<rect x="{cx-12}" y="{cy-12}" width="24" height="24" rx="3" fill="{BADGE}"/>')
    text(cx, cy + 4.6, str(n), 13, 700, "#FFFFFF")


def group(x0, y0, x1, y1, title):
    GRECTS.append((x0, y0, x1, y1, title))
    add(f'<rect x="{x0}" y="{y0}" width="{x1-x0}" height="{y1-y0}" fill="none" '
        f'stroke="{GROUP}" stroke-width="1.3" stroke-dasharray="5 4"/>')
    text(x0 + 14, y0 + 25, title, 14.5, 700, INK, "start")


def boundary(x0, y0, x1, y1):
    add(f'<rect x="{x0}" y="{y0}" width="{x1-x0}" height="{y1-y0}" fill="none" '
        f'stroke="{INK}" stroke-width="1.6"/>')


def aws_tile(x, y, region):
    add(f'<rect x="{x}" y="{y}" width="32" height="32" fill="{INK}"/>')
    text(x + 16, y + 16, "aws", 12, 700, "#FFFFFF")
    add(f'<path d="M {x+7},{y+21} Q {x+16},{y+27} {x+25},{y+21}" fill="none" '
        f'stroke="{ORANGE}" stroke-width="2" stroke-linecap="round"/>')
    add(f'<path d="M {x+21.5},{y+19.5} L {x+25.5},{y+20.5} L {x+24.5},{y+24.5}" '
        f'fill="none" stroke="{ORANGE}" stroke-width="1.6" stroke-linecap="round" '
        f'stroke-linejoin="round"/>')
    cloud_label(x, y, "AWS Cloud", region)


def azure_tile(x, y, region):
    # Official Azure icon bundled with the diagrams package (azure/azure.png).
    add(f'<image x="{x+2}" y="{y+2}" width="28" height="28" xlink:href="{data("azure/azure.png")}"/>')
    cloud_label(x, y, "Microsoft Azure", region)


def cloud_label(x, y, name, region):
    add(f'<text x="{x+44}" y="{y+21}" font-family="{FONT}" font-size="14.5" '
        f'font-weight="700" fill="{INK}">{esc(name)}<tspan dx="10" font-weight="400" '
        f'fill="{TEXT2}">{esc(region)}</tspan></text>')


# ---------------- grid ----------------
WSX0, WSX1 = 40, 360            # workstation column
CX0, CX1 = 400, 1380            # cloud boundary
GX0, GX1 = 425, 1355            # groups inside the cloud
WS = (120, 280)                 # workstation slots
SL = (545, 790, 1020, 1250)     # cloud slots
XB = 1490                       # browser column

# lane 01 (AWS)
L1H, L1T, L1B = 128, 148, 490
RA, RB = 255, 395
# lane 02 (Azure)
L2H, L2T, L2B = 538, 558, 980
RC, RD = 667, 830
YS = 955                        # bottom channel for the state line

add(f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" '
    f'width="{W}" height="{H}" viewBox="0 0 {W} {H}">')
add('<defs>'
    '<marker id="ah" viewBox="0 0 10 10" refX="10" refY="5" markerWidth="6.5" '
    f'markerHeight="6.5" orient="auto"><path d="M0,0 L10,5 L0,10 z" fill="{LINE}"/></marker>'
    '<marker id="ahb" viewBox="0 0 10 10" refX="10" refY="5" markerWidth="5" '
    f'markerHeight="5" orient="auto"><path d="M0,0 L10,5 L0,10 z" fill="{ACCENT}"/></marker>'
    '</defs>')
add(f'<rect width="{W}" height="{H}" fill="#FFFFFF"/>')
text(40, 56, TITLE, 26, 700, INK, "start")
text(40, 82, SUBTITLE, 14, 400, TEXT2, "start")

# ---------------- lane 01: AWS ----------------
text(40, L1H, "01  Native Cloud Monitoring Application with Docker, Kubernetes, AWS",
     17, 700, INK, "start")
group(WSX0, L1T, WSX1, L1B, "Your workstation")
boundary(CX0, L1T, CX1, L1B)
aws_tile(CX0, L1T, "us-east-1")
group(GX0, 190, 665, 470, "Registry and access")
group(695, 190, GX1, 470, "Amazon EKS cluster")

node("flask", "programming/framework/flask.png", WS[0], RA, "Flask app", "app.py, psutil, Plotly")
node("docker", "onprem/container/docker.png", WS[1], RA, "Docker", "image build")
node("ekspy", "programming/language/python.png", WS[1], RB, "eks.py", "Kubernetes client")
node("ecr", "aws/compute/ec2-container-registry.png", SL[0], RA, "Amazon ECR",
     "image repository")
node("iam", "aws/security/identity-and-access-management-iam-role.png", SL[0], RB,
     "AWS IAM", "cluster and node roles")
node("eks", "aws/compute/elastic-kubernetes-service.png", SL[1], RB, "Amazon EKS",
     "cloud-native-cluster")
node("ec2", "aws/compute/ec2.png", SL[2], RB, "Amazon EC2", "node group, t2.micro")
node("deploy", "k8s/compute/deploy.png", SL[2], RA, "Deployment", "my-flask-app pod")
node("svc", "k8s/network/svc.png", SL[3], RA, "Service", "my-flask-service :5000")
node("browser", "aws/general/client.png", XB, RA, "Your browser", "localhost:5000")

link("flask", "r", "docker", "l", "external")
link("docker", "r", "ecr", "l", "external")
link("ekspy", "t", "eks", "t", "external",
     via=[(WS[1], 340), (SL[1], 340)])
link("iam", "r", "eks", "l")
link("eks", "r", "ec2", "l")
link("ec2", "t", "deploy", "b")
link("ecr", "r", "deploy", "l")
link("deploy", "r", "svc", "l")
link("browser", "l", "svc", "r", "external")

text(200, RA - 8, "build, run", 11.5, 400, TEXT2, "middle", halo=True)
text(432, RA - 8, "docker push", 11.5, 400, TEXT2, "start", halo=True)
text(790, RA - 8, "image pull", 11.5, 400, TEXT2, "middle", halo=True)
text(440, 334, "creates deployment and service", 11.5, 400, TEXT2, "start", halo=True)
text(1392, RA - 8, "port-forward", 11.5, 400, TEXT2, "start", halo=True)

# ---------------- lane 02: Azure ----------------
text(40, L2H, "02  Deploy Infrastructure and Assets to Azure using Terraform",
     17, 700, INK, "start")
group(WSX0, L2T, WSX1, L2B, "Your workstation")
boundary(CX0, L2T, CX1, L2B)
azure_tile(CX0, L2T, "eastus")
group(GX0, 602, GX1, 745, "Website resources (main.tf)")
group(GX0, 765, GX1, 905, "Remote state backend")

# The Terraform icon already carries its wordmark, so only the role line is labeled.
node("tf", "onprem/iac/terraform.png", WS[0], RC, "plan, apply, destroy")
node("cli", "azure/other/azure-cloud-shell.png", WS[1], RD, "Azure CLI", "or Cloud Shell")
node("rg1", "azure/general/resourcegroups.png", SL[0], RC, "Resource group", "website")
node("sa1", "azure/storage/storage-accounts.png", SL[1], RC, "Storage account",
     "StorageV2, static website")
node("web", "azure/general/storage-container.png", SL[2], RC, "Container", "$web")
node("html", "azure/general/blob-block.png", SL[3], RC, "Block blob", "index.html")
node("rg2", "azure/general/resourcegroups.png", SL[0], RD, "Resource group", "state")
node("sa2", "azure/storage/storage-accounts.png", SL[1], RD, "Storage account", "state account")
node("con", "azure/general/storage-container.png", SL[2], RD, "Container",
     "private, tfstatecon")
node("state", "azure/general/blob-block.png", SL[3], RD, "Block blob", "terraform.tfstate")

link("tf", "r", "rg1", "l", "external")
link("rg1", "r", "sa1", "l")
link("sa1", "r", "web", "l")
link("web", "r", "html", "l")
link("cli", "r", "rg2", "l", "external")
link("rg2", "r", "sa2", "l")
link("sa2", "r", "con", "l")
link("con", "r", "state", "l")
link("tf", "b", "state", "b", "external", via=[(WS[0], YS), (SL[3], YS)])

text(160, RC - 8, "terraform apply", 11.5, 400, TEXT2, "start", halo=True)
text(432, RD - 8, "az create", 11.5, 400, TEXT2, "start", halo=True)
text(700, YS - 8, "state file stored in the backend", 11.5, 400, TEXT2, "middle", halo=True)

draw_nodes()

# ---------------- step badges (x, y, number), in a gutter beside their line ----------------
for cx, cy, n in [(200, RA - 42, 1), (380, RA - 30, 2), (680, RB + 28, 3), (680, 318, 4),
                  (905, RA - 30, 5), (1385, RA + 26, 6),
                  (380, RD + 28, 7), (380, RC + 28, 8), (1020, YS - 26, 9)]:
    badge(cx, cy, n)

# ---------------- legend ----------------
LY = 1022
STEPS = [
    "Run app.py locally, then build and run it as a Docker image on port 5000.",
    "ecr.py creates an ECR repository with boto3, and docker push uploads the image.",
    "Create the EKS cluster and a t2.micro node group, each with its own IAM role.",
    "eks.py uses the Kubernetes Python client to create the deployment and service.",
    "The pod pulls the image from ECR and runs on the node group.",
    "kubectl port-forward opens the monitoring page at localhost:5000.",
    "The Azure CLI creates the state resource group, storage account, and private container.",
    "terraform plan and apply with dev.tfvars create the website resources and index.html.",
    "Terraform keeps terraform.tfstate in the backend; terraform destroy removes it all.",
]

text(40, LY, "How it works", 16, 700, INK, "start")
per_col = (len(STEPS) + 1) // 2
for i, s in enumerate(STEPS):
    col, row = divmod(i, per_col)
    bx, by = 52 + col * 780, LY + 34 + row * 32
    badge(bx, by, i + 1, record=False)
    text(bx + 22, by + 4.6, s, 13.5, 400, INK, "start")

KEY_Y = LY + 40 + per_col * 32
lx = 40
for k, (color, width, dash, marker, label) in KINDS.items():
    if k not in USED:
        continue
    da = f' stroke-dasharray="{dash}"' if dash else ""
    add(f'<path d="M {lx},{KEY_Y} L {lx+52},{KEY_Y}" stroke="{color}" stroke-width="{width}"'
        f'{da} marker-end="url(#{marker})"/>')
    text(lx + 62, KEY_Y + 4.5, label, 12.5, 400, TEXT2, "start")
    lx += 62 + est_w(label, 12.5) + 48
add("</svg>")
assert KEY_Y + 30 <= H, "canvas too short for the legend: raise H"


# ---------------- checks: keep all of them ----------------
def seg_hits_box(p, q, box, pad=2):
    x0, y0, x1, y1 = box
    (ax, ay), (bx, by) = p, q
    if ay == by:
        lo, hi = sorted((ax, bx))
        return y0 - pad < ay < y1 + pad and lo < x1 + pad and hi > x0 - pad
    lo, hi = sorted((ay, by))
    return x0 - pad < ax < x1 + pad and lo < y1 + pad and hi > y0 - pad


def boxes_overlap(a, b):
    return a[0] < b[2] and b[0] < a[2] and a[1] < b[3] and b[1] < a[3]


def crossings():
    hs = [s for s in SEGS if s[0][1] == s[1][1]]
    vs = [s for s in SEGS if s[0][0] == s[1][0]]
    found = []
    for hp, hq, ha, hb in hs:
        y = hp[1]
        x0, x1 = sorted((hp[0], hq[0]))
        for vp, vq, va, vb in vs:
            if (ha, hb) == (va, vb):
                continue
            x = vp[0]
            y0, y1 = sorted((vp[1], vq[1]))
            if x0 < x < x1 and y0 < y < y1:
                found.append(f"{ha}->{hb} x {va}->{vb}")
    return found


def shared_segments():
    found = []
    for i in range(len(SEGS)):
        for j in range(i + 1, len(SEGS)):
            (p, q, a, b), (r, s, c, d) = SEGS[i], SEGS[j]
            if (a, b) == (c, d):
                continue
            if p[1] == q[1] == r[1] == s[1]:
                lo1, hi1 = sorted((p[0], q[0]))
                lo2, hi2 = sorted((r[0], s[0]))
            elif p[0] == q[0] == r[0] == s[0]:
                lo1, hi1 = sorted((p[1], q[1]))
                lo2, hi2 = sorted((r[1], s[1]))
            else:
                continue
            if min(hi1, hi2) - max(lo1, lo2) > 0:
                found.append(f"{a}->{b} shares a segment with {c}->{d}")
    return found


problems = []
for p, q, a, b in SEGS:
    for k, box in BOX.items():
        if k not in (a, b) and seg_hits_box(p, q, box):
            problems.append(f"line {a}->{b} crosses {k}")
keys = list(BOX)
for i in range(len(keys)):
    for j in range(i + 1, len(keys)):
        if boxes_overlap(BOX[keys[i]], BOX[keys[j]]):
            problems.append(f"label overlap {keys[i]} / {keys[j]}")
for cx, cy, n in BADGES:
    bb = (cx - 12, cy - 12, cx + 12, cy + 12)
    for p, q, a, b in SEGS:
        if seg_hits_box(p, q, bb, pad=1):
            problems.append(f"badge {n} sits on line {a}->{b}")
    for k, box in BOX.items():
        if boxes_overlap(bb, box):
            problems.append(f"badge {n} overlaps {k}")
    for gx0, gy0, gx1, gy1, t in GRECTS:
        tb = (gx0 + 10, gy0 + 8, gx0 + 14 + est_w(t, 14.5) + 4, gy0 + 32)
        if boxes_overlap(bb, tb):
            problems.append(f"badge {n} overlaps group title {t}")
        for edge in ((gx0, gy0, gx1, gy0), (gx0, gy1, gx1, gy1),
                     (gx0, gy0, gx0, gy1), (gx1, gy0, gx1, gy1)):
            if seg_hits_box(edge[:2], edge[2:], bb, pad=1):
                problems.append(f"badge {n} sits on border of {t}")
# labels must sit fully inside the group that holds their icon, clear of the border
for k, (x0, y0, x1, y1) in BOX.items():
    cx, cy = (x0 + x1) / 2, N[k][1]
    for gx0, gy0, gx1, gy1, t in GRECTS:
        if gx0 < cx < gx1 and gy0 < cy < gy1:
            if x0 < gx0 + 4 or x1 > gx1 - 4 or y1 > gy1 - 4 or y0 < gy0 + 34:
                problems.append(f"label of {k} touches its group border ({t})")
# lines must not run through group titles
for p, q, a, b in SEGS:
    for gx0, gy0, gx1, gy1, t in GRECTS:
        tb = (gx0 + 10, gy0 + 8, gx0 + 14 + est_w(t, 14.5) + 4, gy0 + 32)
        if seg_hits_box(p, q, tb):
            problems.append(f"line {a}->{b} runs through group title {t}")
problems += shared_segments()
X = crossings()
if len(X) > 2:
    problems.append(f"{len(X)} line crossings (2 at most, only where unavoidable)")

svg = "\n".join(out)
assert "\u2014" not in svg and "\u2013" not in svg, "em or en dash found"
with open(OUT_SVG, "w") as fh:
    fh.write(svg)
subprocess.run(["rsvg-convert", "-z", "2", "-o", OUT_PNG, OUT_SVG], check=True)
print("nodes:", len(N), "segments:", len(SEGS), "badges:", len(BADGES))
print("crossings:", len(X), *X)
print("layout problems:", problems if problems else "none")
print("wrote", OUT_SVG, "and", OUT_PNG)
