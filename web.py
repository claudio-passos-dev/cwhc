import os, time
from flask import Flask, request, make_response, render_template, redirect
from feedgen.feed import FeedGenerator
from healthck import CloudWalkHealthChecker, Threshold

cwhc = CloudWalkHealthChecker(5, "cloudwalk_healthchecker@mailinator.com")

app = Flask(__name__)

@app.route('/')
def index():
    running = "Start"
    if cwhc.running == True:
        running = "Stop"

    return render_template('index.html', email=cwhc.email, interval=cwhc.interval,
        timeout=cwhc.timeout, hthreshold=cwhc.threshold.health, uthreshold=cwhc.threshold.unhealthy,running=running)

@app.route('/toggle', methods=['POST'])
def toggle():
    if cwhc.running == False:
        cwhc.start()
    else:
        cwhc.stop()
    return redirect('/')

@app.route('/change', methods=['POST'])
def change():
    form = request.form
    cwhc.email = form.get('email')
    cwhc.interval = int(form.get('interval'))
    cwhc.timeout = int(form.get('timeout'))
    uthreshold = int(form.get('uthreshold'))
    hthreshold = int(form.get('hthreshold'))
    cwhc.threshold = Threshold(hthreshold, uthreshold)
    return redirect('/')

@app.route('/rss')
def rss():
    fg = FeedGenerator()
    fg.title('CloudWalk DevSecOps test')
    fg.description('A RSS Feed for HTTP and TCP service')
    fg.docs('')
    fg.generator('')
    fg.link(href='http://example.com')

    with open('log.txt') as f:
        for line in f.readlines():
            info = line.replace('\n', '').split(';')
            fe = fg.add_entry()
            fe.title(f"{info[1]}")
            fe.pubDate(f"{info[0]} GTM-3")
            fe.description(f"server: {info[2]} port:{info[3]}")    

    response = make_response(fg.rss_str())
    response.headers.set('Content-type', 'application/rss+xml')
    return response

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)