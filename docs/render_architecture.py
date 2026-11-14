from pathlib import Path
import html
import cairosvg

OUT = Path(__file__).parent
W, H = 2200, 1320
parts = []

def esc(s): return html.escape(s)

def rect(x, y, w, h, fill, stroke, radius=18, sw=2):
    parts.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{radius}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"/>')

def text(x, y, lines, size=22, color="#0f172a", weight=500, anchor="middle", line_gap=None):
    if isinstance(lines, str): lines = [lines]
    if line_gap is None: line_gap = int(size * 1.28)
    # y is baseline of first line
    spans = ''.join(f'<tspan x="{x}" dy="{0 if i == 0 else line_gap}">{esc(line)}</tspan>' for i, line in enumerate(lines))
    parts.append(f'<text x="{x}" y="{y}" text-anchor="{anchor}" font-family="Arial, Helvetica, sans-serif" font-size="{size}" font-weight="{weight}" fill="{color}">{spans}</text>')

def arrow(x1, y1, x2, y2, label=None, color="#475569", dashed=False, label_x=None, label_y=None, width=3):
    dash = ' stroke-dasharray="9 7"' if dashed else ''
    parts.append(f'<path d="M{x1},{y1} L{x2},{y2}" fill="none" stroke="{color}" stroke-width="{width}"{dash} marker-end="url(#arrow)"/>')
    if label:
        lx = (x1+x2)/2 if label_x is None else label_x
        ly = (y1+y2)/2 - 10 if label_y is None else label_y
        text(lx, ly, label, size=15, color=color, weight=600)

def node(x,y,w,h,fill,stroke,title,sub=None,title_size=22,sub_size=16):
    rect(x,y,w,h,fill,stroke)
    lines=[]
    if isinstance(title, str): lines=[title]
    else: lines=list(title)
    if sub:
        if isinstance(sub,str): sub=[sub]
        lines += list(sub)
    total_h = (len(lines)-1)*int( max(title_size,sub_size)*1.22 )
    base_y = y + h/2 - total_h/2 + max(title_size,sub_size)*0.35
    # first lines title, subsequent sub
    for i,line in enumerate(lines):
        sz = title_size if i < len(title if isinstance(title,list) else [title]) else sub_size
        wt = 700 if i < len(title if isinstance(title,list) else [title]) else 450
        col = "#0f172a" if i < len(title if isinstance(title,list) else [title]) else "#334155"
        text(x+w/2, base_y + i*int(max(title_size,sub_size)*1.22), line, size=sz, color=col, weight=wt)

parts.append(f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">
<defs>
 <marker id="arrow" markerWidth="12" markerHeight="12" refX="10" refY="6" orient="auto" markerUnits="strokeWidth"><path d="M0,0 L12,6 L0,12 z" fill="#475569"/></marker>
 <filter id="shadow" x="-10%" y="-10%" width="120%" height="130%"><feDropShadow dx="0" dy="3" stdDeviation="5" flood-color="#0f172a" flood-opacity="0.10"/></filter>
</defs>
<rect width="100%" height="100%" fill="#ffffff"/>
''')

# Header
text(W/2, 58, "AWS Secrets Management & Credential-Hygiene Detection Lab", size=34, color="#0f172a", weight=750)
text(W/2, 95, "Single AWS account  |  Regional secret monitoring  |  Global IAM event monitoring", size=19, color="#475569", weight=500)

# Identity band
rect(50, 125, 2100, 135, "#f8fafc", "#94a3b8", radius=20, sw=2)
text(85, 158, "IDENTITY & ACCESS", size=17, color="#475569", weight=750, anchor="start")
node(95, 174, 430, 68, "#e0f2fe", "#0284c7", "IAM Identity Center", ["shakthivel-cloudsec"], 21, 15)
node(740, 174, 520, 68, "#eff6ff", "#3b82f6", "SecretsLabOperator", ["Lab administration permission set"], 21, 15)
node(1580, 174, 500, 68, "#eff6ff", "#3b82f6", "SecretsAppReader", ["Read-only access to the lab secret"], 21, 15)
arrow(525, 207, 740, 207, "assigned permission set", label_y=191)
arrow(525, 225, 1580, 225, "assigned permission set", label_y=247)

# Regional panels
rect(50, 295, 1370, 960, "#f8fcff", "#0284c7", radius=24, sw=3)
text(85, 338, "AWS REGION: ap-south-1  |  MUMBAI", size=23, color="#075985", weight=750, anchor="start")
rect(1450, 295, 700, 960, "#fbfaff", "#7c3aed", radius=24, sw=3)
text(1485, 338, "AWS REGION: us-east-1  |  N. VIRGINIA", size=21, color="#5b21b6", weight=750, anchor="start")

# Mumbai top lane: access + rotation
text(85, 383, "SECRET ACCESS & ROTATION", size=16, color="#64748b", weight=750, anchor="start")
node(90, 420, 260, 135, "#e0f2fe", "#0284c7", "Boto3 example client", ["secrets_manager_client.py", "Password redacted in output"], 20, 15)
node(430, 420, 310, 135, "#dcfce7", "#16a34a", "AWS Secrets Manager", ["lab/database/credentials", "Synthetic credential JSON"], 21, 16)
node(820, 405, 375, 165, "#fef3c7", "#d97706", "AWS Lambda", ["secrets-lab-rotation", "createSecret → setSecret", "testSecret → finishSecret", "Backend update/authentication simulated"], 22, 16)
node(1230, 430, 155, 110, "#f1f5f9", "#64748b", "Execution role", ["SecretsRotation", "LambdaRole"], 18, 14)
arrow(350, 487, 430, 487, "GetSecretValue", label_y=465)
arrow(740, 487, 820, 487, "rotation invocation", label_y=465)
arrow(1230, 487, 1195, 487, "assumed by function", dashed=True, label_x=1210, label_y=455)
# operator dotted association
arrow(1000, 242, 1000, 393, "operator configures lab", dashed=True, label_x=1110, label_y=315)
parts.append('<path d="M1830,242 L1830,276 L220,276 L220,420" fill="none" stroke="#64748b" stroke-width="3" stroke-dasharray="9 7" marker-end="url(#arrow)"/>')
text(1000, 269, "reader uses Boto3 client", size=15, color="#64748b", weight=600)

# Mumbai monitoring lane
text(85, 630, "AUDIT, DETECTION & ALERTING", size=16, color="#64748b", weight=750, anchor="start")
node(85, 700, 245, 140, "#ede9fe", "#7c3aed", "AWS CloudTrail", ["Multi-Region management trail", "Audit events"], 21, 15)
node(390, 700, 245, 140, "#ffedd5", "#ea580c", "EventBridge", ["Default event bus", "ap-south-1"], 21, 16)
node(690, 675, 300, 190, "#ffedd5", "#ea580c", "Mumbai detection rules", ["Current-version label change", "Denied GetSecretValue", "Denied secret modification", "Lambda configuration change"], 20, 15)
node(1040, 700, 180, 140, "#fce7f3", "#db2777", "Amazon SNS", ["secrets-security", "-alerts"], 20, 15)
node(1260, 700, 125, 140, "#fdf2f8", "#db2777", "Email", ["Confirmed", "subscription"], 19, 15)
arrow(330, 770, 390, 770, "API events", label_y=748)
arrow(635, 770, 690, 770, "pattern match", label_y=748)
arrow(990, 770, 1040, 770, "matched", label_y=748)
arrow(1220, 770, 1260, 770, "publish", label_y=748)
# CloudTrail and native service event paths
arrow(585, 555, 210, 700, "management API activity", dashed=True, label_x=345, label_y=620)
arrow(585, 555, 510, 700, "Secret Label Updated", color="#16a34a", label_x=610, label_y=645)
arrow(1000, 570, 210, 700, "Lambda API changes", dashed=True, label_x=650, label_y=655)
# S3 archive beneath CloudTrail
node(85, 940, 310, 105, "#ede9fe", "#7c3aed", "S3 CloudTrail log archive", ["secrets-lab trail bucket"], 19, 15)
arrow(205, 840, 205, 940, "log file delivery", label_x=285, label_y=900)
text(450, 990, ["Secret Label Updated events are also matched by EventBridge.", "Rotation stages are synthetic; no live database is connected."], size=16, color="#475569", weight=550, anchor="start", line_gap=26)

# IAM Virginia vertical lane
text(1485, 383, "GLOBAL IAM SERVICE EVENT FLOW", size=16, color="#64748b", weight=750, anchor="start")
node(1530, 420, 540, 100, "#e0e7ff", "#4f46e5", "AWS IAM", ["Global role-policy and trust-policy changes"], 22, 16)
node(1530, 565, 540, 95, "#ede9fe", "#7c3aed", "CloudTrail IAM API event", ["Observed event region: us-east-1"], 20, 16)
node(1530, 705, 540, 95, "#ffedd5", "#ea580c", "EventBridge default event bus", ["us-east-1"], 21, 16)
node(1530, 845, 540, 110, "#ffedd5", "#ea580c", "secrets-lab-iam-role-change", ["Attach / detach / put / delete role policy", "Trust-policy updates"], 21, 16)
node(1530, 1000, 250, 105, "#fce7f3", "#db2777", "Amazon SNS", ["secrets-security", "-alerts-iam"], 20, 15)
node(1820, 1000, 250, 105, "#fdf2f8", "#db2777", "Email", ["Confirmed", "subscription"], 20, 15)
arrow(1800, 520, 1800, 565, "CloudTrail event", label_x=1905, label_y=550)
arrow(1800, 660, 1800, 705, "API Call via CloudTrail", label_x=1940, label_y=690)
arrow(1800, 800, 1800, 845, "pattern match", label_x=1900, label_y=830)
arrow(1800, 955, 1655, 1000, "publish", label_x=1695, label_y=985)
arrow(1780, 1052, 1820, 1052, "email", label_y=1025)
arrow(1260, 242, 1600, 420, "operator manages lab IAM role", dashed=True, label_x=1430, label_y=340)

# Footer note / legend
rect(50, 1180, 2100, 48, "#f1f5f9", "#cbd5e1", radius=12, sw=1)
text(80, 1211, "Scope: one AWS account. Mumbai handles Secrets Manager and Lambda detections; N. Virginia handles IAM global-service events. Never publish real secret values or unredacted identities.", size=16, color="#334155", weight=550, anchor="start")
parts.append('</svg>')
svg = ''.join(parts)
(OUT / 'architecture.svg').write_text(svg, encoding='utf-8')
cairosvg.svg2png(bytestring=svg.encode(), write_to=str(OUT / 'architecture.png'), output_width=W, output_height=H)
