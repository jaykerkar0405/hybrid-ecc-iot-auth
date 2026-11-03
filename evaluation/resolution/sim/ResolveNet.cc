// Copyright (c) 2026 Jay Kerkar, Chaitanya Kelkar, Chirag Poornamath, Yash Kolekar and Shanta Sondur
// SPDX-License-Identifier: Apache-2.0
// OMNeT++ 6 model of device<->server authentication under the BASE Table II environment. Ours, not the BASE authors' code.
// Self-contained network model. The only change: the server's pseudonym-resolution work is read, per number of
// enrolled devices n, from cost_model.csv (written by evaluation/resolution/resolution_costs.py) and priced at tProbe per probe.
#include <omnetpp.h>
#include <algorithm>
#include <cmath>
#include <fstream>
#include <sstream>
#include <string>
#include <vector>

using namespace omnetpp;


class Server;
class Device;

class Core : public cSimpleModule {
  public:
    double rate = 0, range = 0, quantum = 0, handoff = 0, txP = 0, rxP = 0, tProbe = 0, reject = 0, window = 0, advRate = 0;
    int nMsg = 4, bits = 0, W = 13, forgedBits = 128;
    bool lookup = false;
    std::string enrolment, resolver;
    double epochS = 10;
    std::vector<double> honestP, forgedP, epochP, stateB, extraBits;  // indexed by enrolled devices n
    double probesTotal = 0;
    double at(const std::vector<double> &v, int n) const {
        if (v.empty()) return 0;
        if (n < (int)v.size()) return v[n];
        throw cRuntimeError("cost table has no row for n=%d", n);
    }
    void loadCosts() {
        if (resolver == "none") return;
        std::ifstream in(par("costFile").stdstringValue());
        if (!in) throw cRuntimeError("cannot open cost file");
        std::string line; std::getline(in, line);
        while (std::getline(in, line)) {
            std::stringstream ss(line); std::string s, n, h, f, e, b, x;
            std::getline(ss, s, ','); std::getline(ss, n, ','); std::getline(ss, h, ','); std::getline(ss, f, ',');
            std::getline(ss, e, ','); std::getline(ss, b, ','); std::getline(ss, x, ',');
            if (s != resolver) continue;
            size_t i = std::stoul(n);
            for (auto *v : {&honestP, &forgedP, &epochP, &stateB, &extraBits}) if (v->size() <= i) v->resize(i + 1, 0);
            honestP[i] = std::stod(h); forgedP[i] = std::stod(f); epochP[i] = std::stod(e); stateB[i] = std::stod(b); extraBits[i] = std::stod(x);
        }
        if (honestP.empty()) throw cRuntimeError("resolver %s not in cost file", resolver.c_str());
    }
    double devMs = 0, srvMs = 0, speed = 0, area = 1500;
    std::vector<double> lat;
    double bitsOnAir = 0, energyJ = 0;
    long unreachable = 0, completed = 0;
    double lastAct = 0;  // time of the last real activity (the kernel reports the time limit when the queue empties)
    std::vector<Server *> servers;
    std::vector<Device *> devices;
    double q(double t) const { return std::ceil(t / quantum - 1e-9) * quantum; }

  protected:
    void initialize() override {
        rate = par("rateBps"); range = par("rangeM"); quantum = par("quantumS"); handoff = par("handoffS");
        txP = par("txPowerW"); rxP = par("rxPowerW"); tProbe = double(par("tProbeMs")) / 1e3; reject = double(par("rejectMs")) / 1e3;
        window = par("windowS"); advRate = par("adversaryRateHz"); nMsg = par("nMessages"); bits = par("bitsTotal");
        W = par("windowEpochs"); forgedBits = par("forgedBits"); lookup = par("pseudonymLookup");
        enrolment = par("enrolment").stdstringValue();
        resolver = par("resolver").stdstringValue(); epochS = par("epochS");
        loadCosts();
        devMs = par("deviceProcMs"); srvMs = par("serverProcMs"); speed = par("speedMps"); area = par("areaM");
    }
    void finish() override {
        std::vector<double> v = lat;
        std::sort(v.begin(), v.end());
        double mean = 0;
        for (double x : v) mean += x;
        if (!v.empty()) mean /= v.size();
        double p95 = v.empty() ? 0 : v[std::min(v.size() - 1, (size_t)std::ceil(0.95 * v.size()) - 1)];
        recordScalar("latency_mean_ms", mean * 1e3);
        recordScalar("latency_p95_ms", p95 * 1e3);
        recordScalar("sessions_completed", completed);
        recordScalar("sessions_unreachable", unreachable);
        recordScalar("kbit_on_air", bitsOnAir / 1e3);
        recordScalar("energy_mJ", energyJ * 1e3);
        recordScalar("end_time_s", lastAct);
        recordScalar("resolution_probes_total", probesTotal);
    }
};

class Server : public cSimpleModule {
  public:
    double x = 0, y = 0, cpuFree = 0, airFree = 0, busy = 0;
    int enrolled = 0, idx = 0;
    Core *core = nullptr;
    // reserve the shared channel of this server; returns the end of the transmission
    double reserveAir(double now, int nbits) {
        double start = std::max(now, airFree), dur = nbits / core->rate;
        airFree = start + core->q(dur);
        core->bitsOnAir += nbits;
        core->energyJ += (core->txP + core->rxP) * dur;
        return airFree;
    }

  protected:
    int numInitStages() const override { return 3; }
    void initialize(int stage) override;
    void finish() override {
        recordScalar("busy_ms", busy * 1e3); recordScalar("enrolled", enrolled);
        recordScalar("state_bytes", core->at(core->stateB, enrolled));
    }
    void occupy(double now, double work) {
        double start = std::max(now, cpuFree);
        cpuFree = start + core->q(work); busy += work;
        core->lastAct = std::max(core->lastAct, cpuFree);
    }
    void handleMessage(cMessage *msg) override;
};

class Device : public cSimpleModule {
  public:
    double x = 0, y = 0, dist = 0, t0 = 0, vx = 0, vy = 0;
    int srv = -1, phase = 0;
    Core *core = nullptr;
    Server *server = nullptr;

  protected:
    int numInitStages() const override { return 3; }
    void initialize(int stage) override;
    void handleMessage(cMessage *msg) override;
    void sendStep(int step);
    bool selectServer(double px, double py);
};

void Server::initialize(int stage) {
    if (stage == 0) {
        x = par("x").doubleValueInUnit("m"); y = par("y").doubleValueInUnit("m"); idx = getIndex();
        core = check_and_cast<Core *>(getParentModule()->getSubmodule("core"));
        core->servers.push_back(this);
    }
    if (stage == 2) {
        enrolled = 0;
        for (Device *d : core->devices) {
            double dx = d->x - x, dy = d->y - y;
            bool inRange = std::sqrt(dx * dx + dy * dy) <= core->range;
            bool mine = d->srv == idx;
            if (core->enrolment == "reachable" ? inRange : mine) enrolled++;
        }
        if (core->at(core->epochP, enrolled) > 0) {  // O4: one table extension per epoch, at a random phase
            double t = uniform(0, core->epochS);
            if (t < core->window) scheduleAt(core->q(t), new cMessage("epoch"));
        }
    }
}

void Server::handleMessage(cMessage *msg) {
    double now = simTime().dbl();
    if (msg->isSelfMessage()) {  // epoch boundary: extend the pseudonym table
        double probes = core->at(core->epochP, enrolled);
        core->probesTotal += probes;
        occupy(now, probes * core->tProbe);
        delete msg; return;
    }
    cPacket *p = check_and_cast<cPacket *>(msg);
    bool res = core->resolver != "none";
    if (p->hasPar("forged")) {  // adversary request with a random pseudonym
        double probes = res ? core->at(core->forgedP, enrolled) : 0;
        core->probesTotal += probes;
        occupy(now, res ? probes * core->tProbe : core->reject);
        delete p; return;
    }
    int step = p->par("step"), dev = p->par("dev");
    double share = core->srvMs / 1e3 / (core->nMsg / 2);
    double probes = (step == 1 && res) ? core->at(core->honestP, enrolled) : 0.0;  // expected probes, from the measured cost model
    core->probesTotal += probes;
    double work = share + probes * core->tProbe;
    double start = std::max(now, cpuFree), done = start + core->q(work);
    cpuFree = done; busy += work;
    core->lastAct = std::max(core->lastAct, done);
    int bitsMsg = core->bits / core->nMsg;
    Device *d = core->devices[dev];
    double end = reserveAir(done, bitsMsg);  // the reply is sent when the server is done
    cPacket *r = new cPacket("r");
    r->setBitLength(bitsMsg); r->addPar("step") = step + 1;
    sendDirect(r, SimTime(end - now + d->dist / 3e8 + core->handoff), 0, d, "in");
    delete p;
}

void Device::initialize(int stage) {
    if (stage == 0) {
        x = par("x").doubleValueInUnit("m"); y = par("y").doubleValueInUnit("m");
        core = check_and_cast<Core *>(getParentModule()->getSubmodule("core"));
        core->devices.push_back(this);
    }
    if (stage == 1) {
        bool ok = selectServer(x, y);
        if (core->speed > 0) {  // mobile variant: constant velocity in a random direction, reflected at the area border; the server is re-chosen when the session starts
            double a = uniform(0, 6.283185307179586);
            vx = core->speed * std::cos(a); vy = core->speed * std::sin(a);
        } else if (!ok) { core->unreachable++; return; }
        scheduleAt(core->q(uniform(0, core->window)), new cMessage("start"));
    }
}

bool Device::selectServer(double px, double py) {
    double best = 1e18;
    srv = -1; server = nullptr; dist = 0;
    for (Server *s : core->servers) {
        double dx = s->x - px, dy = s->y - py, d = std::sqrt(dx * dx + dy * dy);
        if (d <= core->range && d < best) { best = d; srv = s->idx; server = s; dist = d; }
    }
    return srv >= 0;
}

static double reflect(double v, double L) {
    v = std::fmod(v, 2 * L);
    if (v < 0) v += 2 * L;
    return v <= L ? v : 2 * L - v;
}

void Device::sendStep(int step) {  // device -> server, odd message numbers
    int bitsMsg = core->bits / core->nMsg;
    if (step == 1 && core->resolver != "none") bitsMsg += (int)core->at(core->extraBits, server->enrolled);  // CR, MW: r and per-level tags
    double now = simTime().dbl();
    double end = server->reserveAir(now, bitsMsg);
    cPacket *p = new cPacket("m");
    p->setBitLength(bitsMsg); p->addPar("dev") = getIndex(); p->addPar("step") = step;
    sendDirect(p, SimTime(end - now + dist / 3e8 + core->handoff), 0, server, "in");
}

void Device::handleMessage(cMessage *msg) {
    double share = core->devMs / 1e3 / (core->nMsg / 2 + 1);
    if (msg->isSelfMessage()) {
        std::string n = msg->getName();
        if (n == "start") {
            if (core->speed > 0) {
                double t = simTime().dbl();
                if (!selectServer(reflect(x + vx * t, core->area), reflect(y + vy * t, core->area))) { core->unreachable++; delete msg; return; }
            }
            t0 = simTime().dbl(); phase = 0;
            scheduleAt(simTime() + core->q(share), new cMessage("computed"));
        } else {  // a compute phase finished
            if (phase < core->nMsg / 2) { sendStep(2 * phase + 1); phase++; }
            else { core->lat.push_back(simTime().dbl() - t0); core->completed++;
                core->lastAct = std::max(core->lastAct, simTime().dbl()); }
        }
        delete msg;
        return;
    }
    scheduleAt(simTime() + core->q(share), new cMessage("computed"));  // reply arrived: next compute phase
    delete msg;
}

class Adversary : public cSimpleModule {
    Core *core = nullptr;
    Server *server = nullptr;
    double x = 0, y = 0, dist = 0;

  protected:
    int numInitStages() const override { return 3; }
    void initialize(int stage) override {
        if (stage == 0) {
            x = par("x").doubleValueInUnit("m"); y = par("y").doubleValueInUnit("m");
            core = check_and_cast<Core *>(getParentModule()->getSubmodule("core"));
        }
        if (stage == 1) {
            double best = 1e18;
            for (Server *s : core->servers) {
                double dx = s->x - x, dy = s->y - y, d = std::sqrt(dx * dx + dy * dy);
                if (d <= core->range && d < best) { best = d; server = s; dist = d; }
            }
            if (server && core->advRate > 0) scheduleAt(core->q(exponential(1.0 / core->advRate)), new cMessage("forge"));
        }
    }
    void handleMessage(cMessage *msg) override {
        double now = simTime().dbl();
        if (now >= core->window) { delete msg; return; }
        double end = server->reserveAir(now, core->forgedBits);
        cPacket *p = new cPacket("forged");
        p->setBitLength(core->forgedBits); p->addPar("forged") = 1;
        sendDirect(p, SimTime(end - now + dist / 3e8 + core->handoff), 0, server, "in");
        scheduleAt(simTime() + core->q(exponential(1.0 / core->advRate)), msg);
    }
};

Define_Module(Core);
Define_Module(Server);
Define_Module(Device);
Define_Module(Adversary);

