from pathlib import Path
import html
import cairosvg

OUT = Path(__file__).resolve().parent
W, H = 2400, 1640
parts = []

NAVY = "#14243a"
MUTED = "#52647a"
BLUE = "#1677b8"
PURPLE = "#7156c9"
ORANGE = "#d97706"
GREEN = "#168653"
PINK = "#c02670"
LINE = "#53657b"


def esc(value):
    return html.escape(str(value))


def text(x, y, value, size=26, color=NAVY, weight=500, anchor="middle"):
    parts.append(
        f'<text x="{x}" y="{y}" text-anchor="{anchor}" '
        f'font-family="Arial, Helvetica, sans-serif" font-size="{size}" '
        f'font-weight="{weight}" fill="{color}">{esc(value)}</text>'
    )


def multiline(x, y, lines, size=20, color=MUTED, weight=500, gap=29):
    for index, line in enumerate(lines):
        text(x, y + index * gap, line, size=size, color=color, weight=weight)


def box(x, y, w, h, title, details=(), fill="#ffffff", stroke=BLUE,
        title_size=27, detail_size=19, radius=22):
    parts.append(
        f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{radius}" '
        f'fill="{fill}" stroke="{stroke}" stroke-width="3"/>'
    )
    detail_lines = list(details)
    if detail_lines:
        title_y = y + h / 2 - (len(detail_lines) * 15) - 4
        text(x + w / 2, title_y, title, size=title_size, weight=700)
        multiline(x + w / 2, title_y + 35, detail_lines, size=detail_size, gap=27)
    else:
        text(x + w / 2, y + h / 2 + title_size * 0.35, title,
             size=title_size, weight=700)


def arrow(x1, y1, x2, y2, label=None, color=LINE, dashed=False,
          label_x=None, label_y=None, width=4):
    dash = ' stroke-dasharray="11 9"' if dashed else ''
    parts.append(
        f'<path d="M{x1},{y1} L{x2},{y2}" fill="none" stroke="{color}" '
        f'stroke-width="{width}"{dash} marker-end="url(#arrow)"/>'
    )
    if label:
        lx = (x1 + x2) / 2 if label_x is None else label_x
        ly = (y1 + y2) / 2 - 13 if label_y is None else label_y
        text(lx, ly, label, size=17, color=color, weight=650)


def poly_arrow(points, label=None, label_x=None, label_y=None,
               color=LINE, dashed=True):
    path = " ".join(("M" if i == 0 else "L") + f"{x},{y}" for i, (x, y) in enumerate(points))
    dash = ' stroke-dasharray="11 9"' if dashed else ''
    parts.append(
        f'<path d="{path}" fill="none" stroke="{color}" stroke-width="4"'
        f'{dash} marker-end="url(#arrow)"/>'
    )
    if label:
        text(label_x, label_y, label, size=17, color=color, weight=650)


parts.append(f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">
<defs>
  <marker id="arrow" markerWidth="12" markerHeight="12" refX="10" refY="6" orient="auto" markerUnits="strokeWidth">
    <path d="M0,0 L12,6 L0,12 z" fill="{LINE}"/>
  </marker>
</defs>
<rect width="100%" height="100%" fill="#ffffff"/>
''')

# Title
text(W / 2, 65, "AWS Secrets Management & Credential-Hygiene Detection Lab", size=39, weight=750)
text(W / 2, 108, "Single AWS account  |  Secret lifecycle protection  |  Regional event detection", size=22, color=MUTED)

# Identity band: no intersecting identity arrows or personal username.
parts.append('<rect x="60" y="145" width="2280" height="205" rx="24" fill="#f7f9fc" stroke="#9aabc0" stroke-width="3"/>')
text(95, 185, "IDENTITY & ACCESS", size=20, color=MUTED, weight=750, anchor="start")
box(110, 215, 500, 100, "IAM Identity Center", ["Lab user sign-in"], fill="#e5f3ff", stroke=BLUE)
box(930, 215, 520, 100, "SecretsLabOperator", ["Lab administration permission set"], fill="#edf3ff", stroke="#4779d5", title_size=25)
box(1770, 215, 500, 100, "SecretsAppReader", ["Read-only access to the lab secret"], fill="#edf3ff", stroke="#4779d5", title_size=25)
text(1200, 336, "Identity Center sign-in assigns separate operator and application-reader permission sets", size=17, color=MUTED, weight=600)

# Regional panels
parts.append('<rect x="60" y="390" width="1515" height="1190" rx="26" fill="#f5fbff" stroke="#1484c5" stroke-width="4"/>')
parts.append('<rect x="1605" y="390" width="735" height="1190" rx="26" fill="#faf8ff" stroke="#7758cb" stroke-width="4"/>')
text(105, 445, "AWS REGION: ap-south-1  |  MUMBAI", size=27, color="#075985", weight=750, anchor="start")
text(1650, 445, "AWS REGION: us-east-1  |  N. VIRGINIA", size=24, color="#5b3aad", weight=750, anchor="start")

# Mumbai: secret lifecycle
text(105, 495, "SECRET ACCESS & ROTATION", size=20, color=MUTED, weight=750, anchor="start")
box(105, 555, 330, 180, "Boto3 example client",
    ["secrets_manager_client.py", "Uses SecretsAppReader", "Password redacted in output"],
    fill="#e5f3ff", stroke=BLUE, title_size=24, detail_size=18)
box(565, 555, 360, 180, "AWS Secrets Manager",
    ["lab/database/credentials", "Synthetic credential JSON", "Encrypted secret storage"],
    fill="#e8f8ef", stroke=GREEN, title_size=25, detail_size=18)
box(1060, 555, 390, 180, "AWS Lambda",
    ["secrets-lab-rotation", "createSecret → setSecret", "testSecret → finishSecret", "Backend update/auth simulated"],
    fill="#fff5df", stroke=ORANGE, title_size=27, detail_size=18)
arrow(435, 645, 565, 645, "GetSecretValue", label_y=617)
arrow(925, 645, 1060, 645, "rotation invocation", label_y=617)
box(1095, 770, 320, 90, "Execution role", ["SecretsRotationLambdaRole"],
    fill="#f0f3f7", stroke="#72839a", title_size=22, detail_size=17)
arrow(1255, 770, 1255, 738, "assumed by function", dashed=True, label_x=1390, label_y=758)

# Mumbai: monitoring pipeline
text(105, 925, "AUDIT, DETECTION & ALERTING", size=20, color=MUTED, weight=750, anchor="start")
box(100, 1000, 255, 160, "AWS CloudTrail",
    ["Multi-Region management", "event trail"], fill="#f0ebff", stroke=PURPLE, title_size=25, detail_size=18)
box(430, 1000, 245, 160, "EventBridge",
    ["Default event bus", "ap-south-1"], fill="#fff1df", stroke=ORANGE, title_size=25, detail_size=18)
box(750, 970, 335, 220, "Mumbai detection rules",
    ["Current-version label change", "Denied GetSecretValue", "Denied secret modification", "Lambda configuration change"],
    fill="#fff1df", stroke=ORANGE, title_size=24, detail_size=17, radius=20)
box(1155, 1000, 165, 160, "Amazon SNS",
    ["secrets-security-", "alerts"], fill="#fdebf4", stroke=PINK, title_size=24, detail_size=17)
box(1370, 1000, 150, 160, "Email",
    ["Confirmed", "subscription"], fill="#fff0f7", stroke=PINK, title_size=24, detail_size=18)
arrow(355, 1080, 430, 1080, "events", label_y=985)
arrow(675, 1080, 750, 1080, "match", label_y=985)
arrow(1085, 1080, 1155, 1080, "alert", label_y=985)
arrow(1320, 1080, 1370, 1080, "email", label_y=985)

# CloudTrail archive and clear native event path.
box(100, 1295, 300, 115, "S3 log archive",
    ["CloudTrail management logs"], fill="#f0ebff", stroke=PURPLE, title_size=23, detail_size=17)
arrow(225, 1160, 225, 1295, "log file delivery", label_x=330, label_y=1240)
poly_arrow([(745, 735), (745, 890), (552, 890), (552, 1000)],
           label="Secret Label Updated event", label_x=690, label_y=880,
           color=GREEN, dashed=True)
text(445, 1322, "Lambda API changes are audited by CloudTrail and matched by the", size=17, color=MUTED, anchor="start")
text(445, 1350, "Lambda configuration-change rule in the Mumbai event pipeline.", size=17, color=MUTED, anchor="start")
text(445, 1408, "Rotation is a four-stage Secrets Manager workflow; backend update", size=17, color=MUTED, anchor="start")
text(445, 1436, "and database authentication are simulated in this lab.", size=17, color=MUTED, anchor="start")

# Virginia: global IAM detection, vertical and uncluttered.
text(1650, 495, "GLOBAL IAM SERVICE EVENT FLOW", size=20, color=MUTED, weight=750, anchor="start")
box(1700, 555, 545, 120, "AWS IAM",
    ["Global role-policy and trust-policy changes"], fill="#e9eaff", stroke="#6259d6", title_size=27, detail_size=19)
box(1700, 725, 545, 115, "CloudTrail IAM API event",
    ["Observed event region: us-east-1"], fill="#f0ebff", stroke=PURPLE, title_size=25, detail_size=19)
box(1700, 890, 545, 115, "EventBridge default event bus",
    ["us-east-1"], fill="#fff1df", stroke=ORANGE, title_size=25, detail_size=19)
box(1700, 1055, 545, 150, "secrets-lab-iam-role-change",
    ["Attach / detach / put / delete role policy", "Trust-policy updates"],
    fill="#fff1df", stroke=ORANGE, title_size=24, detail_size=18)
box(1680, 1300, 250, 145, "Amazon SNS",
    ["secrets-security-", "alerts-iam"], fill="#fdebf4", stroke=PINK, title_size=24, detail_size=18)
box(2000, 1300, 250, 145, "Email",
    ["Confirmed", "subscription"], fill="#fff0f7", stroke=PINK, title_size=25, detail_size=18)
arrow(1972, 675, 1972, 725, "CloudTrail event", label_x=2100, label_y=708)
arrow(1972, 840, 1972, 890, "API Call via CloudTrail", label_x=2140, label_y=875)
arrow(1972, 1005, 1972, 1055, "pattern match", label_x=2080, label_y=1040)
poly_arrow([(1972, 1205), (1972, 1250), (1805, 1250), (1805, 1300)],
           label="publish", label_x=1875, label_y=1240, dashed=False)
arrow(1930, 1372, 2000, 1372, "email", label_y=1347)

# Footer
parts.append('<rect x="60" y="1510" width="2280" height="45" rx="12" fill="#eef2f7" stroke="#bdc8d6" stroke-width="2"/>')
text(90, 1540,
     "Scope: one AWS account. Mumbai handles secret and Lambda detections; N. Virginia handles IAM global-service events. No live database is connected.",
     size=17, color="#35465b", weight=600, anchor="start")
parts.append('</svg>')

svg = ''.join(parts)
svg_path = OUT / "architecture.svg"
png_path = OUT / "architecture.png"
svg_path.write_text(svg, encoding="utf-8")
cairosvg.svg2png(bytestring=svg.encode("utf-8"), write_to=str(png_path), output_width=W, output_height=H)
print(f"Generated {png_path}")
print(f"Generated {svg_path} (local source; do not commit unless desired)")
