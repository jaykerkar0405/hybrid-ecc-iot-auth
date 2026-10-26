// Re-implementation (ours, NOT the code of the BASE authors) of the BASE Table II environment in plain OMNeT++ (no INET, no SUMO).

simple Core
{
    parameters:
        // --- BASE Table II ---
        double rateBps = default(10e6);           // bandwidth of the channel or link: 10 Mbps
        double rangeM = default(500);             // XBee coverage 500 (line of sight) .. 800 m (obstructed)
        double quantumS = default(15e-6);         // "sampling interval of device" 15 us, used as the event-time quantum
        double handoffS = default(10e-9);         // hand-off time 10 ns
        double speedMps = default(0);             // BASE Table II: device speed (max) 160 km/h = 44.44 m/s; 0 = static (BASE Sec. V text)
        double areaM = default(1500);
        double txPowerW = default(0.0756);        // energy for packet transmission 75.6 mW
        double rxPowerW = default(0.0756);        // energy for packet receiving 75.6 mW
        // --- scheme under test (generated from the paper tables by scripts/gen_omnet_ini.py) ---
        string scheme = default("unset");
        int nMessages = default(4);               // messages per session
        int bitsTotal;                            // bits on air per session (BASE Table IV total)
        double deviceProcMs;                      // device compute per session
        double serverProcMs;                      // server compute per session
        bool pseudonymLookup = default(false);    // proposed scheme only: server scans N_s x W pseudonyms
        int windowEpochs = default(13);
        double tProbeMs = default(0.0);           // one pseudonym probe (SHA-256) on the server
        double rejectMs = default(0.0);           // server cost to reject a forged request (not a full scan)
        // --- run-level assumptions (NOT given by BASE) ---
        string enrolment = default("reachable");  // reachable: server resolves every device in range; nearest: only attached devices
        double windowS = default(10);             // each device authenticates once at a uniform time in [0, windowS]
        double adversaryRateHz = default(1);      // forged requests per second per adversary
        int forgedBits = default(128);
}

simple Device
{
    parameters:
        double x @unit(m) = default(uniform(0m, 1500m));
        double y @unit(m) = default(uniform(0m, 1500m));
    gates:
        input in @directIn;
}

simple Server
{
    parameters:
        double x @unit(m) = default(uniform(0m, 1500m));
        double y @unit(m) = default(uniform(0m, 1500m));
    gates:
        input in @directIn;
}

simple Adversary
{
    parameters:
        double x @unit(m) = default(uniform(0m, 1500m));
        double y @unit(m) = default(uniform(0m, 1500m));
}

network AuthNet
{
    parameters:
        int numDevices;                           // 100 .. 1000
        double serverFraction = default(0.05);    // Table II: 5 %
        double adversaryFraction = default(0.05); // Table II: "randomly generated"; this share is OUR assumption
        int numServers = default(max(1, int(floor(serverFraction * numDevices + 0.5))));
        int numAdversaries = default(int(floor(adversaryFraction * numDevices + 0.5)));
    submodules:
        core: Core;
        devices[numDevices]: Device;
        servers[numServers]: Server;
        adversaries[numAdversaries]: Adversary;
}
