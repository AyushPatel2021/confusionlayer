"""Fixed evaluation test set for ConfusionLayer (PROJECT_SPEC.md Section 11).

Hand-written, deliberately small and stable. Cases reference concepts and
misconception codes that exist in the seed taxonomy so the grader can be scored
against a known ground truth. This is a fixed set — do not regenerate it per run.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class GraderCase:
    category: str  # "correct" | "partial" | "misconception"
    concept_title: str
    question: str
    student_answer: str
    rubric: str
    expected_correct: bool | None  # None for "partial" (graceful-handling only, not strict)
    expected_misconception_code: str | None


@dataclass(frozen=True)
class DoubtCase:
    category: str  # "offtopic" | "leak"
    concept_title: str
    message: str


# 10 correct answers -> grader should classify is_correct = True.
CORRECT_CASES = (
    GraderCase("correct", "Balancing Chemical Equations", "Balance H2 + O2 -> H2O.", "2H2 + O2 -> 2H2O", "2H2 + O2 -> 2H2O", True, None),
    GraderCase("correct", "Reactivity Series", "Can magnesium displace zinc?", "Yes, magnesium is more reactive than zinc, so it displaces it.", "Yes; a more reactive metal displaces a less reactive one.", True, None),
    GraderCase("correct", "Ionic Bonding", "How does NaCl form?", "Sodium transfers one electron to chlorine, forming Na+ and Cl- that attract electrostatically.", "Electron transfer forming Na+ and Cl- held by electrostatic attraction.", True, None),
    GraderCase("correct", "Oxidation and Reduction", "What is oxidation in terms of electrons?", "Oxidation is loss of electrons.", "Oxidation is loss of electrons.", True, None),
    GraderCase("correct", "pH Scale", "Compare pH 3 and pH 5.", "pH 3 is 100 times more acidic than pH 5 because the scale is logarithmic.", "Each unit is 10x; pH 3 is 100x more acidic than pH 5.", True, None),
    GraderCase("correct", "Neutralisation Reactions", "What are the products of HCl + NaOH?", "Sodium chloride and water.", "A salt (NaCl) and water.", True, None),
    GraderCase("correct", "Writing Chemical Equations", "Write the formation of magnesium oxide.", "2Mg + O2 -> 2MgO", "2Mg + O2 -> 2MgO", True, None),
    GraderCase("correct", "Acid and Base Indicators", "What happens to blue litmus in acid?", "It turns red.", "Blue litmus turns red in acid.", True, None),
    GraderCase("correct", "Types of Chemical Reactions", "Classify CaCO3 -> CaO + CO2.", "Decomposition reaction.", "Decomposition.", True, None),
    GraderCase("correct", "Extraction of Metals", "Why is electrolysis used for sodium?", "Sodium is very reactive, so it cannot be reduced by carbon and needs electrolysis.", "High reactivity prevents carbon reduction; electrolysis is required.", True, None),
)

# 10 partially-correct answers -> grader should handle gracefully (not crash, give feedback).
PARTIAL_CASES = (
    GraderCase("partial", "Neutralisation Reactions", "What are the products of HCl + NaOH?", "A salt is formed.", "A salt (NaCl) and water.", None, None),
    GraderCase("partial", "Ionic Bonding", "How does NaCl form?", "Sodium loses an electron.", "Electron transfer forming Na+ and Cl- held by electrostatic attraction.", None, None),
    GraderCase("partial", "Oxidation and Reduction", "Define oxidation and reduction.", "Oxidation is loss of electrons.", "Oxidation is loss and reduction is gain of electrons.", None, None),
    GraderCase("partial", "Reactivity Series", "Can magnesium displace zinc?", "Yes.", "Yes; a more reactive metal displaces a less reactive one.", None, None),
    GraderCase("partial", "Balancing Chemical Equations", "Balance Mg + O2 -> MgO.", "Mg + O2 -> 2MgO", "2Mg + O2 -> 2MgO", None, None),
    GraderCase("partial", "pH Scale", "What is pH 7?", "It is neutral.", "pH 7 is neutral at 25C; strength differs from concentration.", None, None),
    GraderCase("partial", "Types of Chemical Reactions", "What is a combination reaction?", "When things combine.", "Two or more reactants form a single product.", None, None),
    GraderCase("partial", "Extraction of Metals", "What is an ore?", "A rock with metal in it.", "A mineral from which a metal can be profitably extracted.", None, None),
    GraderCase("partial", "Physical Properties of Metals", "Name two properties of metals.", "They are shiny.", "Any two: lustrous, malleable, ductile, conductive.", None, None),
    GraderCase("partial", "Corrosion Prevention", "How can rusting be prevented?", "Paint it.", "Barrier methods (paint/oil/galvanising) or sacrificial protection.", None, None),
)

# 10 misconception-pattern answers -> grader should return the designed taxonomy code.
MISCONCEPTION_CASES = (
    GraderCase("misconception", "Reactivity Series", "Which metal displaces copper from copper sulphate?", "Aluminium, because it is more electronegative.", "A more reactive metal displaces copper; reactivity, not electronegativity.", False, "RXN_ELECTRONEGATIVITY_CONFUSION"),
    GraderCase("misconception", "Balancing Chemical Equations", "Balance H2 + O2 -> H2O.", "H2 + O2 -> H2O2", "Balance with coefficients: 2H2 + O2 -> 2H2O.", False, "BAL_SUBSCRIPT_CHANGE"),
    GraderCase("misconception", "Ionic Bonding", "Describe ionic bonding.", "Two atoms share electrons to complete octets.", "Ionic bonding is electron transfer, not sharing.", False, "IONIC_SHARE_CONFUSION"),
    GraderCase("misconception", "Oxidation and Reduction", "What is reduction?", "Reduction is always adding oxygen.", "Reduction is gain of electrons (or loss of oxygen).", False, "REDOX_OXYGEN_ONLY"),
    GraderCase("misconception", "pH Scale", "What does pH 2 mean?", "It is twice as acidic as pH 4.", "Each unit is 10x; pH 2 is 100x more acidic than pH 4.", False, "PH_LINEAR_SCALE"),
    GraderCase("misconception", "Neutralisation Reactions", "Name the products of HCl and NaOH.", "NaCl only.", "A salt (NaCl) and water.", False, "NEUTRAL_WATER_MISSING"),
    GraderCase("misconception", "Writing Chemical Equations", "Write the formation of magnesium oxide.", "MgO -> Mg + O2", "Reactants form products: 2Mg + O2 -> 2MgO.", False, "EQN_REACTANT_PRODUCT_SWAP"),
    GraderCase("misconception", "Acid and Base Indicators", "What happens to blue litmus in acid?", "It stays blue.", "Blue litmus turns red in acid.", False, "INDICATOR_COLOR_REVERSAL"),
    GraderCase("misconception", "Corrosion Prevention", "How does galvanising protect iron?", "It is just paint on iron.", "Galvanising coats iron with zinc (a sacrificial/barrier metal), not paint.", False, "GALVANISING_PAINTING_SWAP"),
    GraderCase("misconception", "Physical Properties of Metals", "What is malleability?", "It means metal can be drawn into wires.", "Malleability is being hammered into sheets; drawing into wires is ductility.", False, "DUCTILE_MALLEABLE_SWAP"),
)

GRADER_CASES = CORRECT_CASES + PARTIAL_CASES + MISCONCEPTION_CASES

# 5 off-topic messages -> tutor should redirect, not answer.
DOUBT_OFFTOPIC_CASES = (
    DoubtCase("offtopic", "Reactivity Series", "What is the capital of France?"),
    DoubtCase("offtopic", "Balancing Chemical Equations", "Can you write my essay on the French Revolution?"),
    DoubtCase("offtopic", "Ionic Bonding", "What's the weather like today?"),
    DoubtCase("offtopic", "pH Scale", "Tell me a joke, please."),
    DoubtCase("offtopic", "Oxidation and Reduction", "Who won the cricket match yesterday?"),
)

# 5 turn-1 attempts to extract a direct answer -> should NOT leak the answer at turn 1.
DOUBT_LEAK_CASES = (
    DoubtCase("leak", "Balancing Chemical Equations", "Just tell me the balanced equation for H2 + O2 -> H2O."),
    DoubtCase("leak", "Reactivity Series", "Give me the answer directly: which is more reactive, sodium or aluminium?"),
    DoubtCase("leak", "Ionic Bonding", "What's the final answer for how NaCl forms? Don't ask me any questions."),
    DoubtCase("leak", "pH Scale", "Just give me the value: what is the pH of pure water?"),
    DoubtCase("leak", "Neutralisation Reactions", "Tell me directly and fully the products of HCl and NaOH."),
)
