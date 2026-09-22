# Architecture Deep Dive: The Force-Directed PCB Engine

While most "AI PCB Generators" simply prompt an LLM to output a block of KiCad S-expressions, CircuitPilot takes a fundamentally different, physics-based approach to ensure the output is actually routable and manufacturable.

LLMs are excellent at logic and extraction, but they are notoriously terrible at spatial reasoning and geometry. Asking an LLM to place 50 components on a 2D grid so that their traces don't cross is a recipe for failure.

To solve this, CircuitPilot offloads the spatial reasoning entirely to a **Custom Native Python Routing Engine**.

---

## 1. The Physics Placement (Force-Directed Graph)

Instead of rigid grid placement, we treat the circuit as a physical system of springs and magnets.

- **Repulsion (Coulomb's Law)**: Every component naturally repels every other component. This prevents components from stacking on top of each other and naturally forces them to spread out across the PCB area.
- **Attraction (Hooke's Law)**: When two components are connected by an electrical net (e.g., `GND`, `3V3`, or an I2C trace), a virtual "spring" is attached between them. The more connections two components share, the stronger the spring.
- **Simulated Annealing**: The engine runs a physics simulation. Initially, the "temperature" is high, and components fly around the board rapidly. As the temperature cools, the springs pull connected components tightly together, while the repulsive forces maintain a safe DRC margin between their physical footprints.

The result is a completely organic placement where electrically related components automatically cluster together (like decoupling capacitors physically hugging the VCC pins of an MCU), exactly as a human engineer would do.

## 2. Net-Aware Ratsnest Routing

Once the components settle, the engine routes the copper traces.

- **Shortest-First Strategy**: The router analyzes the ratsnest (the web of unrouted connections) and sorts them by Euclidean distance. It routes the shortest paths first, ensuring that complex, long-distance signal traces don't block critical local connections.
- **IPC-2152 Trace Widths**: The LLM `Critic` tags nets with their power requirements. The routing engine dynamically selects the trace width (e.g., 0.8mm for `VCC`/`GND` and 0.25mm for `SDA`/`SCL`).
- **45-Degree Chamfering**: Traces aren't drawn as direct straight lines. The engine implements a pathfinding algorithm that limits trace angles to 45 degrees, mimicking professional EDA routing aesthetics and preventing acid traps during fabrication.
- **Multi-Layer Escaping**: If a trace cannot find a path on the Front Copper (`F.Cu`), the engine automatically spawns a Drill Via and tunnels the trace through the Bottom Copper (`B.Cu`), allowing complex boards to resolve themselves.

## 3. The Critic (Self-Verification)

Before the Physics engine even boots up, the LLM `Planner` passes its component manifest to a second LLM agent: the `Critic`.

The `Critic` is prompted specifically with IPC design rules and common electrical engineering pitfalls. 
- It checks if the MCU has the required decoupling capacitors.
- It verifies if LEDs have current-limiting resistors.
- It ensures pull-up resistors exist on I2C lines.

If the `Planner` forgot any of these, the `Critic` forces a revision. Only a validated, electrically sound manifest is passed to the physics engine.

---

### Why this matters

By decoupling the *logic* (LLM) from the *geometry* (Physics Engine), CircuitPilot achieves what standard wrapper-agents cannot: real, manufacturable hardware from a single natural language prompt.
