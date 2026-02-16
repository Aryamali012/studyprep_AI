// Subjects database for various competitive exams
const subjectsData = {
    JEE: {
        "Physics": [
            "Mechanics", "Thermodynamics", "Waves & Oscillations", "Optics",
            "Electrostatics", "Current Electricity", "Magnetism", "Electromagnetic Induction",
            "Modern Physics", "Semiconductor & Electronics"
        ],
        "Chemistry": [
            "Physical Chemistry - Basics", "Atomic Structure", "Chemical Bonding",
            "Thermodynamics & Thermochemistry", "Chemical Equilibrium", "Ionic Equilibrium",
            "Electrochemistry", "Chemical Kinetics", "Organic Chemistry - Basics",
            "Hydrocarbons", "Alcohols, Phenols & Ethers", "Aldehydes & Ketones",
            "Coordination Compounds", "Periodic Table & Properties"
        ],
        "Mathematics": [
            "Algebra", "Trigonometry", "Coordinate Geometry", "Calculus - Limits & Continuity",
            "Differentiation", "Integration", "Differential Equations", "Vectors & 3D Geometry",
            "Probability & Statistics", "Matrices & Determinants", "Complex Numbers",
            "Sequences & Series", "Permutations & Combinations"
        ]
    },

    NEET: {
        "Physics": [
            "Mechanics", "Thermodynamics", "Waves & Sound", "Optics",
            "Electrostatics", "Current Electricity", "Magnetism",
            "Modern Physics", "Dual Nature of Matter"
        ],
        "Chemistry": [
            "Physical Chemistry", "Atomic Structure", "Chemical Bonding",
            "Thermodynamics", "Equilibrium", "Electrochemistry",
            "Organic Chemistry", "Biomolecules", "Polymers",
            "Inorganic Chemistry", "Periodic Table", "Coordination Compounds"
        ],
        "Biology": [
            "Cell Biology", "Genetics & Evolution", "Human Physiology",
            "Plant Physiology", "Ecology & Environment", "Biotechnology",
            "Animal Kingdom", "Plant Kingdom", "Reproduction",
            "Molecular Basis of Inheritance", "Human Health & Disease"
        ]
    },

    GATE: {
        CS: {
            "Engineering Mathematics": [
                "Discrete Mathematics", "Linear Algebra", "Probability & Statistics",
                "Calculus", "Numerical Methods"
            ],
            "Digital Logic": [
                "Boolean Algebra", "Combinational Circuits", "Sequential Circuits",
                "Number Systems"
            ],
            "Computer Organization": [
                "Machine Instructions", "Addressing Modes", "CPU Design",
                "Memory Hierarchy", "I/O Interface", "Pipelining"
            ],
            "Data Structures & Algorithms": [
                "Arrays & Linked Lists", "Stacks & Queues", "Trees & Binary Trees",
                "Graphs", "Hashing", "Sorting & Searching", "Algorithm Design",
                "Complexity Analysis"
            ],
            "Operating Systems": [
                "Process Management", "Memory Management", "File Systems",
                "CPU Scheduling", "Deadlocks", "Synchronization"
            ],
            "Databases": [
                "ER Model", "Relational Model", "SQL", "Normalization",
                "Transactions", "Indexing"
            ],
            "Computer Networks": [
                "OSI & TCP/IP Models", "Data Link Layer", "Network Layer",
                "Transport Layer", "Application Layer"
            ],
            "Theory of Computation": [
                "Finite Automata", "Context-Free Grammars", "Turing Machines",
                "Undecidability", "Regular Languages"
            ],
            "Compiler Design": [
                "Lexical Analysis", "Parsing", "Syntax Directed Translation",
                "Code Generation", "Code Optimization"
            ]
        },
        EC: {
            "Engineering Mathematics": [
                "Linear Algebra", "Calculus", "Differential Equations",
                "Probability & Statistics", "Complex Variables"
            ],
            "Networks & Signals": [
                "Network Theory", "Signals & Systems", "Control Systems"
            ],
            "Electronic Devices": [
                "Semiconductor Physics", "Diodes & BJTs", "MOSFETs", "Op-Amps"
            ],
            "Analog Circuits": [
                "Amplifiers", "Oscillators", "Feedback Circuits"
            ],
            "Digital Circuits": [
                "Boolean Algebra", "Combinational Circuits", "Sequential Circuits",
                "Microprocessors"
            ],
            "Communications": [
                "Analog Communication", "Digital Communication", "Information Theory"
            ],
            "Electromagnetics": [
                "Maxwell's Equations", "Transmission Lines", "Waveguides", "Antennas"
            ]
        },
        ME: {
            "Engineering Mathematics": [
                "Linear Algebra", "Calculus", "Differential Equations",
                "Probability & Statistics", "Numerical Methods"
            ],
            "Engineering Mechanics": [
                "Statics", "Dynamics", "Friction"
            ],
            "Strength of Materials": [
                "Stress & Strain", "Bending", "Torsion", "Columns"
            ],
            "Thermodynamics": [
                "Laws of Thermodynamics", "Cycles", "Properties of Gases"
            ],
            "Fluid Mechanics": [
                "Fluid Statics", "Fluid Dynamics", "Dimensional Analysis"
            ],
            "Manufacturing": [
                "Casting", "Machining", "Welding", "Metal Forming"
            ]
        },
        EE: {
            "Engineering Mathematics": [
                "Linear Algebra", "Calculus", "Differential Equations",
                "Complex Variables", "Probability"
            ],
            "Electric Circuits": [
                "Network Analysis", "Transient Analysis", "AC Circuits"
            ],
            "Electromagnetic Fields": [
                "Electrostatics", "Magnetostatics", "Maxwell's Equations"
            ],
            "Signals & Systems": [
                "LTI Systems", "Fourier Analysis", "Laplace Transform", "Z-Transform"
            ],
            "Electrical Machines": [
                "Transformers", "DC Machines", "Induction Motors", "Synchronous Machines"
            ],
            "Power Systems": [
                "Power Generation", "Transmission Lines", "Load Flow", "Protection"
            ],
            "Control Systems": [
                "Transfer Functions", "Stability Analysis", "Root Locus", "Bode Plots"
            ]
        },
        CE: {
            "Engineering Mathematics": [
                "Linear Algebra", "Calculus", "Differential Equations", "Probability"
            ],
            "Structural Engineering": [
                "Mechanics of Solids", "Structural Analysis", "RCC Design", "Steel Design"
            ],
            "Geotechnical Engineering": [
                "Soil Mechanics", "Foundation Engineering"
            ],
            "Water Resources": [
                "Fluid Mechanics", "Hydraulics", "Hydrology", "Irrigation"
            ],
            "Environmental Engineering": [
                "Water Supply", "Sewage Treatment", "Air Pollution"
            ],
            "Transportation Engineering": [
                "Highway Engineering", "Traffic Engineering"
            ]
        }
    },

    CAT: {
        "Quantitative Aptitude": [
            "Number Systems", "Arithmetic", "Algebra", "Geometry & Mensuration",
            "Modern Math", "Permutations & Combinations", "Probability"
        ],
        "Verbal Ability & Reading Comprehension": [
            "Reading Comprehension", "Para Jumbles", "Sentence Completion",
            "Critical Reasoning", "Vocabulary", "Grammar"
        ],
        "Data Interpretation & Logical Reasoning": [
            "Tables & Charts", "Bar & Pie Charts", "Line Graphs",
            "Logical Reasoning", "Puzzles & Arrangements", "Set Theory",
            "Venn Diagrams"
        ]
    },

    UPSC: {
        "General Studies I": [
            "Indian History", "World History", "Indian Geography",
            "Society & Social Issues"
        ],
        "General Studies II": [
            "Indian Polity & Governance", "International Relations",
            "Social Justice", "Constitution"
        ],
        "General Studies III": [
            "Indian Economy", "Science & Technology", "Environment & Ecology",
            "Internal Security", "Disaster Management"
        ],
        "General Studies IV": [
            "Ethics & Integrity", "Aptitude", "Case Studies",
            "Emotional Intelligence"
        ],
        "CSAT": [
            "Reading Comprehension", "Logical Reasoning", "Quantitative Aptitude",
            "Decision Making", "Data Interpretation"
        ]
    },

    IELTS: {
        "Listening": [
            "Section 1 - Conversation", "Section 2 - Monologue",
            "Section 3 - Academic Discussion", "Section 4 - Academic Lecture",
            "Note Completion", "Multiple Choice", "Matching"
        ],
        "Reading": [
            "Passage Analysis", "True/False/Not Given", "Matching Headings",
            "Summary Completion", "Multiple Choice", "Sentence Completion"
        ],
        "Writing": [
            "Task 1 - Data Description", "Task 1 - Letter Writing",
            "Task 2 - Essay Writing", "Coherence & Cohesion",
            "Grammar & Vocabulary"
        ],
        "Speaking": [
            "Part 1 - Introduction", "Part 2 - Long Turn",
            "Part 3 - Discussion", "Fluency & Pronunciation"
        ]
    }
};
