"""World Seed – Layer 1: static human-world facts per Piaget stage.

Provides a curated "initial world package" of facts, regularities,
and causal rules that bootstrap the Being's world model without
requiring real user interactions.

Each stage contains facts organized by domain from the Human World
Envelope.  Facts are structured as short declarative statements with
concrete examples and counterexamples.

References:
    - Piaget sensorimotor: object permanence, causality
    - Piaget preoperational: symbolic thought, egocentrism
    - Piaget concrete operational: conservation, classification
    - Piaget formal operational: hypothetical-deductive reasoning
"""

from __future__ import annotations

import logging

from serhu_orchestrator.curriculum.types import WorldSeedFact
from serhu_orchestrator.personality.types import STAGE_ORDER

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Fact definitions – organized by stage and domain
# ---------------------------------------------------------------------------

def _sensorimotor_facts() -> list[WorldSeedFact]:
    """Facts for the sensorimotor stage (0-24 months equivalent).

    Focus: physical objects, permanence, simple causality,
    basic sensory experiences, and primitive social bonds.
    """
    facts: list[WorldSeedFact] = []
    _id = 0

    def _add(domain: str, fact: str, examples: list[str], counterexamples: list[str] | None = None) -> None:
        nonlocal _id
        _id += 1
        facts.append(WorldSeedFact(
            fact_id=f"sensorimotor_{_id:03d}",
            stage="sensorimotor",
            domain=domain,
            fact=fact,
            examples=examples,
            counterexamples=counterexamples or [],
        ))

    # -- everyday_objects --
    _add("everyday_objects", "Objects exist even when you cannot see them.",
         ["A ball hidden under a blanket is still there.", "Mama leaves the room but comes back."],
         ["Sounds disappear when they stop."])
    _add("everyday_objects", "A ball is round and can roll.",
         ["Push a ball and it rolls away.", "A round apple can roll too."],
         ["A block does not roll easily."])
    _add("everyday_objects", "A cup can hold water inside it.",
         ["Pour water into a cup and it stays.", "Milk fills the cup."],
         ["A plate cannot hold water well."])
    _add("everyday_objects", "A spoon is used for eating.",
         ["Scoop food with a spoon.", "Stir with a spoon."],
         ["You do not cut with a spoon."])
    _add("everyday_objects", "A blanket is soft and warm.",
         ["Cover yourself with a blanket to feel warm.", "A teddy bear is also soft."],
         ["A block is hard, not soft."])
    _add("everyday_objects", "Food gives energy when you eat it.",
         ["Eat an apple and feel better.", "Drink milk and feel full."],
         ["A toy cannot be eaten."])
    _add("everyday_objects", "Water is wet and can be poured.",
         ["Pour water from a cup.", "Water splashes when it falls."],
         ["A block is dry and cannot be poured."])
    _add("everyday_objects", "A toy can be picked up and put down.",
         ["Pick up a rattle and shake it.", "Put a block on the table."],
         ["A table is too heavy to pick up."])
    _add("everyday_objects", "A door opens and closes.",
         ["Push the door to open it.", "Pull the door to close it."],
         ["A wall does not open."])
    _add("everyday_objects", "Light makes things visible.",
         ["Turn on the light to see.", "Sunlight comes through the window."],
         ["In the dark, things are hard to see."])
    _add("everyday_objects", "Bread is food that can be eaten.",
         ["Eat a piece of bread.", "Bread is soft to touch."],
         ["A shoe is not food."])
    _add("everyday_objects", "A bottle holds liquid.",
         ["Fill a bottle with water.", "Drink milk from a bottle."],
         ["A shoe does not hold liquid."])
    _add("everyday_objects", "A chair is for sitting.",
         ["Sit on the chair.", "The chair has legs."],
         ["A ball is not for sitting."])
    _add("everyday_objects", "A shoe goes on a foot.",
         ["Put shoes on to walk outside.", "Shoes come in pairs."],
         ["A hat does not go on a foot."])

    # -- space_time --
    _add("space_time", "Things that are dropped fall down.",
         ["Drop a ball and it falls to the floor.", "Release a spoon and it drops."],
         ["A balloon floats up."])
    _add("space_time", "Objects can be near or far.",
         ["The cup is near me on the table.", "The door is far across the room."],
         ["Something cannot be near and far at the same time."])
    _add("space_time", "Things can be inside or outside a container.",
         ["The toy is inside the box.", "The ball is outside the box."],
         [])
    _add("space_time", "If something goes away, it can come back.",
         ["Mama leaves and comes back.", "A ball rolls away and can be brought back."],
         ["Broken things may not come back."])
    _add("space_time", "Up is above and down is below.",
         ["The light is up on the ceiling.", "The floor is down below."],
         [])
    _add("space_time", "Things happen one after another.",
         ["First cry, then mama comes.", "First eat, then sleep."],
         [])
    _add("space_time", "When something is gone, it can return.",
         ["A hidden toy can be found again.", "Night ends and day comes back."],
         ["Eaten food does not come back."])
    _add("space_time", "Here means close, there means far.",
         ["The toy is here in my hands.", "The ball is over there."],
         [])

    # -- physical_actions --
    _add("physical_actions", "If you push something, it moves.",
         ["Push a ball and it rolls.", "Push a door and it opens."],
         ["Push a wall and nothing happens."])
    _add("physical_actions", "If you drop something, it falls.",
         ["Drop a spoon and it hits the floor.", "Let go of a ball and it drops."],
         ["A balloon may float instead of fall."])
    _add("physical_actions", "Shaking a rattle makes noise.",
         ["Shake the rattle and hear a sound.", "Shake a bell and it rings."],
         ["Shake a blanket and there is no sound."])
    _add("physical_actions", "Pulling brings things closer.",
         ["Pull a toy toward you.", "Pull a blanket over yourself."],
         ["Pulling a wall does not move it."])
    _add("physical_actions", "Throwing sends things away from you.",
         ["Throw a ball and it goes far.", "Throw a toy and it lands somewhere."],
         [])
    _add("physical_actions", "Grabbing holds things in your hand.",
         ["Grab a spoon to eat.", "Hold a bottle to drink."],
         ["You cannot grab water."])
    _add("physical_actions", "Hitting something makes a sound.",
         ["Hit the table and hear a thump.", "Clap hands and hear a clap."],
         ["Hit a pillow and the sound is quiet."])
    _add("physical_actions", "Opening reveals what is inside.",
         ["Open a box to see the toy.", "Open the door to see outside."],
         ["Opening an empty box reveals nothing."])
    _add("physical_actions", "Looking at something lets you see it.",
         ["Look at the ball to see its color.", "Look at mama's face."],
         ["You cannot see things behind you without turning."])
    _add("physical_actions", "Touching tells you how something feels.",
         ["Touch the blanket — it feels soft.", "Touch the block — it feels hard."],
         [])
    _add("physical_actions", "Eating makes hunger go away.",
         ["Eat bread and feel full.", "Drink milk when thirsty."],
         ["Eating a toy does not help."])
    _add("physical_actions", "Crying signals discomfort or need.",
         ["Cry when hungry.", "Cry when cold or scared."],
         ["Laughing signals happiness, not discomfort."])

    # -- social_routines --
    _add("social_routines", "Mama and papa provide comfort.",
         ["Mama holds you when you cry.", "Papa's voice is soothing."],
         ["A stranger may not provide the same comfort."])
    _add("social_routines", "Smiling means someone is happy.",
         ["Mama smiles when she sees you.", "Smile back at a friendly face."],
         ["Not all smiles mean happiness."])
    _add("social_routines", "Waving means hello or goodbye.",
         ["Wave hello when someone arrives.", "Wave bye-bye when someone leaves."],
         [])
    _add("social_routines", "Hugging is a sign of affection.",
         ["Mama hugs you to comfort you.", "Hug your teddy bear."],
         [])
    _add("social_routines", "Peek-a-boo teaches that people come back.",
         ["Someone hides their face, then reveals it.", "The person is still there behind their hands."],
         [])
    _add("social_routines", "Saying 'no' means to stop.",
         ["Mama says 'no' when you reach for something dangerous.", "'No' means do not do that."],
         [])
    _add("social_routines", "Responding to your name means they want your attention.",
         ["Someone calls your name and looks at you.", "Turn toward the voice when your name is called."],
         [])

    # -- tasks_and_rules --
    _add("tasks_and_rules", "Same things look alike.",
         ["Two red balls look the same.", "Two cups of the same shape match."],
         ["A ball and a block look different."])
    _add("tasks_and_rules", "More means a bigger amount.",
         ["More blocks in a pile is more.", "More milk in the cup is more."],
         ["A bigger cup does not always mean more milk."])
    _add("tasks_and_rules", "Doing the same thing again gives the same result.",
         ["Drop the ball again and it falls again.", "Push the button again and the light turns on again."],
         ["Sometimes things break and the result changes."])
    _add("tasks_and_rules", "One and two are small numbers.",
         ["One ball. Two balls.", "Hold one toy in each hand."],
         [])

    # -- communication --
    _add("communication", "Sounds carry meaning.",
         ["Mama's voice means mama is near.", "A loud bang means something fell."],
         ["Random noise may not have meaning."])
    _add("communication", "Repeating a sound can get a response.",
         ["Say 'ma-ma' and mama responds.", "Babble and someone talks back."],
         [])
    _add("communication", "Pointing at something communicates interest.",
         ["Point at a toy you want.", "Point at something new to show curiosity."],
         [])
    _add("communication", "Words name things.",
         ["'Ball' means the round toy.", "'Mama' means the caring person."],
         ["Not every sound is a word."])

    return facts


def _preoperational_facts() -> list[WorldSeedFact]:
    """Facts for the preoperational stage (24-84 months equivalent).

    Focus: categories, symbolic thought, simple language,
    'why' questions, routines, and basic intentions.
    """
    facts: list[WorldSeedFact] = []
    _id = 0

    def _add(domain: str, fact: str, examples: list[str], counterexamples: list[str] | None = None) -> None:
        nonlocal _id
        _id += 1
        facts.append(WorldSeedFact(
            fact_id=f"preoperational_{_id:03d}",
            stage="preoperational",
            domain=domain,
            fact=fact,
            examples=examples,
            counterexamples=counterexamples or [],
        ))

    # -- everyday_objects --
    _add("everyday_objects", "Objects can be grouped by color.",
         ["All red things go together.", "Sort crayons by color."],
         ["A red ball and a red car are different objects despite same color."])
    _add("everyday_objects", "Objects come in different sizes: big and small.",
         ["A big ball and a small ball.", "A big dog and a small dog."],
         ["Size can be relative — a small horse is bigger than a big dog."])
    _add("everyday_objects", "Some things are alive and some are not.",
         ["A dog is alive. A toy dog is not.", "Flowers are alive. Plastic flowers are not."],
         ["It is hard to tell if something very small, like a seed, is alive."])
    _add("everyday_objects", "Food can be sweet, salty, or sour.",
         ["An apple is sweet.", "A lemon is sour.", "Chips are salty."],
         ["Water has no strong taste."])
    _add("everyday_objects", "Books contain stories and pictures.",
         ["Open a book to see a story.", "Picture books have images."],
         ["Not all books have pictures."])
    _add("everyday_objects", "A mirror shows your reflection.",
         ["Look in the mirror to see yourself.", "The mirror shows what is in front of it."],
         ["A window is not the same as a mirror."])
    _add("everyday_objects", "Clothes are for wearing.",
         ["A hat goes on your head.", "A coat keeps you warm."],
         ["You do not wear a plate."])
    _add("everyday_objects", "Tools help you do things.",
         ["A brush helps you paint.", "Scissors help you cut paper."],
         ["A ball is not a tool."])
    _add("everyday_objects", "Things can be made of different materials.",
         ["A cup can be plastic or glass.", "A toy can be wood or plastic."],
         [])
    _add("everyday_objects", "Some objects are fragile and can break.",
         ["A glass cup can break if dropped.", "An egg is fragile."],
         ["A rubber ball does not break when dropped."])

    # -- space_time --
    _add("space_time", "Morning comes before afternoon, afternoon before night.",
         ["Wake up in the morning.", "Eat lunch in the afternoon.", "Sleep at night."],
         ["In some places, it is light at night in summer."])
    _add("space_time", "Yesterday happened before today, tomorrow comes after.",
         ["Yesterday we went to the park.", "Tomorrow we will play."],
         [])
    _add("space_time", "Fast things move quickly, slow things move slowly.",
         ["A car is fast.", "A snail is slow."],
         ["A car can also be slow in traffic."])
    _add("space_time", "Left and right are opposite directions.",
         ["Raise your left hand.", "Turn right to go to the kitchen."],
         ["Left and right depend on which way you face."])
    _add("space_time", "Seasons change throughout the year.",
         ["Summer is warm.", "Winter is cold.", "Autumn has falling leaves."],
         ["Not all places have four seasons."])
    _add("space_time", "Day has sunlight, night has darkness.",
         ["The sun shines during the day.", "Stars appear at night."],
         ["Clouds can make daytime dark."])
    _add("space_time", "Things in front of you are easier to see than things behind.",
         ["Look forward to see the TV.", "Turn around to see what is behind."],
         [])

    # -- physical_actions --
    _add("physical_actions", "Running is faster than walking.",
         ["Run to the playground to get there faster.", "Walk slowly to the store."],
         ["A fast walker may be faster than a slow runner."])
    _add("physical_actions", "Drawing creates pictures on paper.",
         ["Use a crayon to draw a house.", "Paint a flower with a brush."],
         ["Drawing on a wall may not be allowed."])
    _add("physical_actions", "Building with blocks creates structures.",
         ["Stack blocks to build a tower.", "Arrange blocks to make a wall."],
         ["If the tower is too tall, it may fall."])
    _add("physical_actions", "Pouring moves liquid from one container to another.",
         ["Pour water from a jug to a glass.", "Pour juice into a cup."],
         ["If you pour too much, it spills."])
    _add("physical_actions", "Climbing lets you reach higher places.",
         ["Climb the stairs to go up.", "Climb a tree to see from above."],
         ["Climbing can be dangerous without care."])
    _add("physical_actions", "Hiding makes you hard to find.",
         ["Hide behind the couch.", "Cover your face to hide."],
         ["If your feet show, you are not well hidden."])
    _add("physical_actions", "Mixing combines things together.",
         ["Mix colors to make a new color.", "Mix flour and water to make dough."],
         ["Mixed things are hard to separate."])
    _add("physical_actions", "Kicking sends a ball forward.",
         ["Kick the ball to a friend.", "Kick a ball into the goal."],
         ["Kicking a wall hurts your foot."])

    # -- social_routines --
    _add("social_routines", "Saying 'please' is polite when asking.",
         ["'Can I have water, please?'", "'Please pass the crayons.'"],
         ["Demanding without 'please' may seem rude."])
    _add("social_routines", "Saying 'thank you' shows gratitude.",
         ["'Thank you for the food.'", "'Thank you for playing with me.'"],
         [])
    _add("social_routines", "Saying 'sorry' means you regret what happened.",
         ["'Sorry for breaking the cup.'", "'Sorry I made you sad.'"],
         ["Saying sorry without meaning it is not genuine."])
    _add("social_routines", "Friends play together and share.",
         ["Share toys with a friend.", "Take turns on the swing."],
         ["Not everyone wants to share all the time."])
    _add("social_routines", "Family members care for each other.",
         ["Parents take care of children.", "Siblings play together."],
         ["Family members can also disagree."])
    _add("social_routines", "Feeling happy makes you want to smile.",
         ["You smile when you get a present.", "Laughing at a funny joke."],
         ["You can smile even when pretending."])
    _add("social_routines", "Feeling sad can make you want to cry.",
         ["Cry when a toy breaks.", "Feel sad when a friend leaves."],
         ["Sometimes people are sad but do not cry."])
    _add("social_routines", "Feeling angry happens when things go wrong.",
         ["Feel angry when someone takes your toy.", "Get frustrated when you can't do something."],
         ["Anger passes with time."])
    _add("social_routines", "Everyone has a name.",
         ["My name is special to me.", "Call people by their name."],
         [])
    _add("social_routines", "Helping others makes them feel good.",
         ["Help carry the groceries.", "Help a friend build a tower."],
         ["Not all help is wanted."])

    # -- tasks_and_rules --
    _add("tasks_and_rules", "Things can be sorted by shape: circle, square, triangle.",
         ["Round things are circles.", "Boxes are shaped like squares."],
         ["Not everything fits a simple shape."])
    _add("tasks_and_rules", "Counting goes 1, 2, 3, 4, 5...",
         ["Count your fingers: 1, 2, 3, 4, 5.", "Count the blocks in the tower."],
         ["Skipping a number gives the wrong count."])
    _add("tasks_and_rules", "Matching means finding things that are the same.",
         ["Match the red card with another red card.", "Match shoes in pairs."],
         ["Two things can match on color but differ in size."])
    _add("tasks_and_rules", "Patterns repeat in a predictable way.",
         ["Red, blue, red, blue is a pattern.", "Clap, stomp, clap, stomp."],
         ["Random arrangements are not patterns."])
    _add("tasks_and_rules", "First, second, third describe order.",
         ["I finished first!", "She was second in line."],
         [])
    _add("tasks_and_rules", "Categories group things that are similar.",
         ["Animals: dog, cat, bird.", "Fruits: apple, banana, orange."],
         ["A tomato is tricky — fruit or vegetable?"])
    _add("tasks_and_rules", "Rules tell you what to do and what not to do.",
         ["Rule: wash hands before eating.", "Rule: no running indoors."],
         ["Rules can be changed by the people who make them."])
    _add("tasks_and_rules", "Numbers tell you how many things there are.",
         ["There are 3 apples on the table.", "I have 5 fingers on each hand."],
         [])

    # -- communication --
    _add("communication", "'Why?' asks for a reason.",
         ["'Why is the sky blue?'", "'Why do birds fly?'"],
         ["Sometimes there is no simple answer to 'why'."])
    _add("communication", "'What?' asks for identification.",
         ["'What is this?'", "'What color is the ball?'"],
         [])
    _add("communication", "'How?' asks about a process.",
         ["'How do you make a cake?'", "'How does a car move?'"],
         [])
    _add("communication", "Telling a story describes events in order.",
         ["'First the bear woke up. Then he ate breakfast.'"],
         ["A jumbled story is confusing."])
    _add("communication", "Asking a question expects an answer.",
         ["'Where is the cat?' 'Under the table.'"],
         ["Rhetorical questions do not expect a real answer."])
    _add("communication", "Pretend play uses imagination.",
         ["Pretend the box is a spaceship.", "Pretend to be a doctor."],
         ["Pretend is not the same as real."])
    _add("communication", "Describing uses words to tell what something is like.",
         ["'The ball is red and round.'", "'The cat is fluffy and small.'"],
         ["A description can be incomplete."])
    _add("communication", "True means it matches reality, false means it does not.",
         ["'The sky is blue' is true.", "'Dogs can fly' is false."],
         ["Some things are hard to classify as simply true or false."])

    return facts


def _concrete_operational_facts() -> list[WorldSeedFact]:
    """Facts for the concrete operational stage (84-132 months equivalent).

    Focus: rules, sequences, conservation, classification,
    multi-step problems, and logical reasoning about concrete things.
    """
    facts: list[WorldSeedFact] = []
    _id = 0

    def _add(domain: str, fact: str, examples: list[str], counterexamples: list[str] | None = None) -> None:
        nonlocal _id
        _id += 1
        facts.append(WorldSeedFact(
            fact_id=f"concrete_{_id:03d}",
            stage="concrete_operational",
            domain=domain,
            fact=fact,
            examples=examples,
            counterexamples=counterexamples or [],
        ))

    # -- everyday_objects --
    _add("everyday_objects", "The amount of water stays the same when poured into a different shaped container.",
         ["Pour water from a tall glass to a wide bowl — same amount.", "The shape changes but volume is conserved."],
         ["If you spill some water during pouring, the amount changes."])
    _add("everyday_objects", "Objects can be classified by multiple properties simultaneously.",
         ["Sort buttons by color AND size.", "Group animals by habitat AND diet."],
         ["Sometimes categories overlap."])
    _add("everyday_objects", "Materials have measurable properties: weight, length, temperature.",
         ["A ruler measures length.", "A scale measures weight.", "A thermometer measures temperature."],
         ["Color cannot be measured with a ruler."])
    _add("everyday_objects", "Tools are designed for specific functions.",
         ["A hammer is for hitting nails.", "A saw is for cutting wood."],
         ["A hammer is not ideal for cutting."])
    _add("everyday_objects", "Ingredients combine to create products.",
         ["Flour + water + yeast → bread.", "Paint colors mix to make new colors."],
         ["Not all combinations produce useful results."])
    _add("everyday_objects", "Some changes are reversible, others are not.",
         ["Freezing water into ice is reversible (melt it).", "Cooking an egg is not reversible."],
         [])
    _add("everyday_objects", "Weight is conserved: a ball of clay weighs the same when flattened.",
         ["Reshape clay without adding or removing any.", "The weight on the scale stays the same."],
         ["If you tear off a piece, the weight changes."])
    _add("everyday_objects", "Number is conserved regardless of arrangement.",
         ["5 coins in a line = 5 coins in a circle.", "Spreading things apart does not change the count."],
         [])

    # -- space_time --
    _add("space_time", "Events can be placed on a timeline in chronological order.",
         ["Monday comes before Tuesday.", "Breakfast happens before lunch."],
         ["In different time zones, events happen at different times."])
    _add("space_time", "Distance can be measured in standard units.",
         ["The park is 2 kilometers away.", "The table is 1 meter long."],
         ["'Far' is subjective — 2 km is far for walking, short for driving."])
    _add("space_time", "Speed equals distance divided by time.",
         ["A car traveling 60 km in 1 hour goes 60 km/h.", "Running 100 meters in 10 seconds is fast."],
         ["Speed can change during the journey."])
    _add("space_time", "Schedules organize activities in time.",
         ["School starts at 8 AM.", "The bus comes every 30 minutes."],
         ["Schedules can be disrupted by unexpected events."])
    _add("space_time", "Maps represent spaces from above.",
         ["A map shows streets and buildings.", "North is usually at the top of a map."],
         ["Maps are simplified — not every detail is shown."])
    _add("space_time", "Seasons follow a predictable cycle.",
         ["Spring → Summer → Autumn → Winter → Spring.", "Each season lasts about 3 months."],
         ["Tropical regions may not have distinct seasons."])

    # -- physical_actions --
    _add("physical_actions", "Following a sequence of steps produces a result.",
         ["Recipe: 1. Mix flour. 2. Add water. 3. Knead. 4. Bake.", "Assembly: step 1, step 2, step 3."],
         ["Skipping steps may cause failure."])
    _add("physical_actions", "Comparing two objects reveals similarities and differences.",
         ["Both are round, but one is bigger.", "Both are red, but one is heavier."],
         [])
    _add("physical_actions", "Sorting puts things in order by a property.",
         ["Sort sticks from shortest to longest.", "Order numbers from smallest to largest."],
         ["Different properties give different orders."])
    _add("physical_actions", "Balancing requires equal weight on both sides.",
         ["A seesaw balances when both sides weigh the same.", "Add weight to the light side to balance."],
         ["Moving the fulcrum also changes balance."])
    _add("physical_actions", "Transforming an object changes its form but may preserve its substance.",
         ["Mold clay into a snake — still clay.", "Cut paper into strips — still paper."],
         ["Burning paper transforms it into ash — different substance."])
    _add("physical_actions", "Measuring uses standard units for accuracy.",
         ["Use a ruler to measure exactly 10 cm.", "Use a timer to measure exactly 5 minutes."],
         ["Guessing is less accurate than measuring."])

    # -- social_routines --
    _add("social_routines", "Rules make games fair for everyone.",
         ["In soccer, you cannot use your hands.", "In board games, everyone takes turns."],
         ["Not everyone agrees on all rules."])
    _add("social_routines", "Cooperation means working together toward a shared goal.",
         ["Build a fort together.", "Clean the room as a team."],
         ["Cooperation fails if one person does not contribute."])
    _add("social_routines", "Fairness means everyone gets an equal chance.",
         ["Each person gets the same number of candies.", "Everyone plays for the same amount of time."],
         ["'Fair' does not always mean 'equal' (someone may need more help)."])
    _add("social_routines", "Responsibility means doing what you are supposed to do.",
         ["It is your responsibility to do homework.", "Clean up after yourself."],
         ["Taking on too many responsibilities can be overwhelming."])
    _add("social_routines", "Trust is built through consistent actions.",
         ["If someone always keeps promises, you trust them.", "Being reliable builds trust."],
         ["One broken promise can damage trust."])
    _add("social_routines", "Disagreements can be resolved through discussion.",
         ["Talk about the problem calmly.", "Listen to the other person's view."],
         ["Not all disagreements are easily resolved."])
    _add("social_routines", "Different people have different perspectives.",
         ["You like blue, your friend likes red.", "What is easy for you may be hard for someone else."],
         [])
    _add("social_routines", "Apologizing sincerely helps repair relationships.",
         ["Say sorry and explain what you will do differently.", "Accept the apology gracefully."],
         ["An empty apology does not repair trust."])

    # -- tasks_and_rules --
    _add("tasks_and_rules", "Classification organizes things into categories and subcategories.",
         ["Animals: mammals, birds, reptiles.", "Mammals: dogs, cats, horses."],
         ["Some animals are hard to classify (platypus)."])
    _add("tasks_and_rules", "Seriation arranges things in a logical order.",
         ["Order 5 sticks by length.", "Rank 10 numbers from smallest to largest."],
         ["Without a clear criterion, ordering is subjective."])
    _add("tasks_and_rules", "If-then rules describe conditional logic.",
         ["If it rains, then bring an umbrella.", "If you study, then you learn more."],
         ["If-then does not always work (if you study, you might still forget)."])
    _add("tasks_and_rules", "Addition and subtraction are inverse operations.",
         ["5 + 3 = 8, and 8 - 3 = 5.", "Adding and then removing the same amount returns to the start."],
         [])
    _add("tasks_and_rules", "A procedure is a sequence of steps to follow.",
         ["Step 1: read the problem. Step 2: identify the question. Step 3: solve.", "Follow a recipe step by step."],
         ["Procedures may need adaptation for different situations."])
    _add("tasks_and_rules", "Exceptions are cases that do not follow the general rule.",
         ["Most birds fly, but penguins do not.", "Most mammals live on land, but whales live in water."],
         [])
    _add("tasks_and_rules", "Comparing quantities uses greater than, less than, or equal.",
         ["7 > 5.", "3 < 8.", "4 = 4."],
         [])
    _add("tasks_and_rules", "Multi-step problems require solving sub-problems first.",
         ["To find total cost: count items, then multiply by price.", "To plan a trip: choose destination, then route, then pack."],
         ["If a sub-step is wrong, the final answer is wrong."])

    # -- communication --
    _add("communication", "Explaining means giving reasons and evidence.",
         ["'I think it will rain because the clouds are dark.'", "'Plants need water because they absorb it through roots.'"],
         ["'Because I said so' is not a good explanation."])
    _add("communication", "Summarizing captures the main idea in fewer words.",
         ["The story is about a fox who outsmarts a crow.", "The experiment showed that plants need light."],
         ["A summary that is too short may miss important details."])
    _add("communication", "Comparing shows how things are alike or different.",
         ["Dogs and cats are both pets, but dogs bark and cats meow.", "Summer and winter are both seasons but have opposite temperatures."],
         [])
    _add("communication", "'Because' connects a cause to its effect.",
         ["'The floor is wet because someone spilled water.'", "'I am hungry because I skipped breakfast.'"],
         ["Correlation is not always causation."])
    _add("communication", "'However' introduces a contrasting idea.",
         ["'Dogs are loyal. However, they need a lot of care.'", "'The test was hard. However, most students passed.'"],
         [])
    _add("communication", "Asking for clarification helps understanding.",
         ["'Can you explain what you mean?'", "'Do you mean X or Y?'"],
         [])
    _add("communication", "Evidence supports or refutes a claim.",
         ["'I know it rained because the ground is wet.'", "'The data shows an increase in temperature.'"],
         ["Weak evidence does not prove a claim."])

    return facts


def _formal_operational_facts() -> list[WorldSeedFact]:
    """Facts for the formal operational stage (132+ months equivalent).

    Focus: hypothetical reasoning, abstractions, analogies,
    systematic planning, and metacognition.
    """
    facts: list[WorldSeedFact] = []
    _id = 0

    def _add(domain: str, fact: str, examples: list[str], counterexamples: list[str] | None = None) -> None:
        nonlocal _id
        _id += 1
        facts.append(WorldSeedFact(
            fact_id=f"formal_{_id:03d}",
            stage="formal_operational",
            domain=domain,
            fact=fact,
            examples=examples,
            counterexamples=counterexamples or [],
        ))

    # -- everyday_objects --
    _add("everyday_objects", "Every designed object embodies trade-offs between function, cost, and aesthetics.",
         ["A ceramic mug is beautiful but fragile.", "Plastic is cheap but less sustainable."],
         ["Some designs achieve all three well."])
    _add("everyday_objects", "Technology evolves through iteration and improvement.",
         ["Phones evolved from landlines to smartphones.", "Cars became more fuel-efficient over decades."],
         ["Not all changes are improvements."])
    _add("everyday_objects", "Sustainability considers long-term environmental impact.",
         ["Reusable bags reduce waste.", "Solar panels reduce fossil fuel use."],
         ["Producing solar panels also has environmental costs."])
    _add("everyday_objects", "Systems are composed of interdependent parts.",
         ["A clock has gears, hands, and a power source working together.", "An ecosystem has producers, consumers, and decomposers."],
         ["Removing one part may or may not break the whole system."])
    _add("everyday_objects", "The function of an object depends on its context.",
         ["A knife is a tool in the kitchen but a weapon in other contexts.", "Water is essential for life but dangerous in floods."],
         [])

    # -- space_time --
    _add("space_time", "Perspective changes how the same event is interpreted.",
         ["A rainy day is bad for a picnic but good for farmers.", "Losing a game teaches resilience despite feeling bad."],
         [])
    _add("space_time", "Historical patterns can inform predictions about the future.",
         ["Economic cycles suggest recessions follow booms.", "Seasonal patterns predict weather trends."],
         ["Past performance does not guarantee future results."])
    _add("space_time", "Probability quantifies how likely an event is.",
         ["A fair coin has 50% chance of heads.", "The probability of rain tomorrow is 70%."],
         ["Low probability does not mean impossible."])
    _add("space_time", "Causality can have multiple contributing factors.",
         ["A traffic accident may be caused by speed, weather, and distraction.", "Academic success depends on effort, ability, and resources."],
         ["Identifying all causes is often difficult."])
    _add("space_time", "Planning involves anticipating future states and obstacles.",
         ["Plan a project: set goals, identify risks, create milestones.", "Plan a trip: budget, schedule, contingencies."],
         ["Plans must be flexible because reality is uncertain."])
    _add("space_time", "Time management balances urgency and importance.",
         ["Urgent and important tasks come first.", "Important but not urgent tasks should not be neglected."],
         ["Focusing only on urgent tasks leads to neglecting long-term goals."])

    # -- physical_actions --
    _add("physical_actions", "Experiments test hypotheses by controlling variables.",
         ["Change one variable and keep others constant.", "Compare results with and without the variable."],
         ["Uncontrolled experiments yield unreliable results."])
    _add("physical_actions", "Optimization finds the best solution within constraints.",
         ["Maximize output while minimizing cost.", "Find the shortest route considering time and fuel."],
         ["Optimal for one criterion may not be optimal for another."])
    _add("physical_actions", "Iterative refinement improves results through repeated cycles.",
         ["Draft → review → revise → final.", "Prototype → test → improve → production."],
         ["Over-iterating without clear goals wastes resources."])
    _add("physical_actions", "Models simplify reality to make it understandable.",
         ["A map is a model of terrain.", "A diagram is a model of a process."],
         ["All models are simplifications — some important details may be lost."])
    _add("physical_actions", "Simulation predicts outcomes without real-world consequences.",
         ["Flight simulators train pilots without risk.", "Weather models predict storms."],
         ["Simulations are only as good as their assumptions."])

    # -- social_routines --
    _add("social_routines", "Empathy involves understanding another person's feelings and perspective.",
         ["Imagine how a friend feels after losing a pet.", "Consider why a coworker is stressed."],
         ["Empathy is different from sympathy (feeling sorry for someone)."])
    _add("social_routines", "Ethical dilemmas have no single correct answer.",
         ["Should you tell a harsh truth or a kind lie?", "Is it ethical to break a small rule to help someone?"],
         ["Simple right/wrong thinking does not work for dilemmas."])
    _add("social_routines", "Compromise involves each side giving up something.",
         ["Split chores in a way both agree on.", "Choose a vacation spot both partners enjoy."],
         ["Compromise may leave both sides partially unsatisfied."])
    _add("social_routines", "Identity is shaped by experiences, choices, and relationships.",
         ["Your values are influenced by your upbringing.", "Your identity evolves as you grow."],
         ["Identity is not fixed — it changes throughout life."])
    _add("social_routines", "Cultural context influences behavior and expectations.",
         ["Greetings differ across cultures.", "What is polite in one culture may be rude in another."],
         ["Universal human values exist despite cultural differences."])
    _add("social_routines", "Conflict resolution requires active listening and mutual respect.",
         ["Repeat back what the other person said to show understanding.", "Acknowledge valid points on both sides."],
         ["Ignoring the conflict does not resolve it."])
    _add("social_routines", "Leadership involves guiding and empowering others, not just commanding.",
         ["A good leader listens to feedback.", "Empowering team members builds trust."],
         ["Authoritarian leadership may get short-term results but damages relationships."])

    # -- tasks_and_rules --
    _add("tasks_and_rules", "Hypotheses must be testable and falsifiable.",
         ["'Plants grow faster with more light' can be tested.", "'This is the best color' is subjective and not testable."],
         [])
    _add("tasks_and_rules", "Variables can be independent, dependent, or controlled.",
         ["Independent: what you change. Dependent: what you measure. Controlled: what stays the same."],
         ["Confounding variables can invalidate results."])
    _add("tasks_and_rules", "Deductive reasoning goes from general rules to specific conclusions.",
         ["All mammals breathe air. Whales are mammals. Therefore, whales breathe air."],
         ["If the general rule is wrong, the conclusion is wrong."])
    _add("tasks_and_rules", "Inductive reasoning goes from specific observations to general rules.",
         ["Every swan I've seen is white → all swans are white.", "The sun rose every day so far → it will rise tomorrow."],
         ["A single counterexample can disprove an induction (black swan)."])
    _add("tasks_and_rules", "Abstraction removes unnecessary detail to focus on essentials.",
         ["A map abstracts terrain into simple symbols.", "An algorithm abstracts a solution into steps."],
         ["Too much abstraction loses important information."])
    _add("tasks_and_rules", "Generalization applies a principle from specific cases to broader ones.",
         ["Gravity applies to all objects, not just apples.", "Rules of arithmetic work for any numbers."],
         ["Over-generalization leads to stereotypes and errors."])
    _add("tasks_and_rules", "Strategy involves choosing among alternatives based on expected outcomes.",
         ["In chess, choose the move that maximizes future options.", "In business, weigh risk vs. reward."],
         ["The best strategy depends on incomplete information."])
    _add("tasks_and_rules", "Evaluation uses criteria to judge quality.",
         ["Rate a solution by correctness, efficiency, and clarity.", "Judge an argument by evidence and logic."],
         ["Different evaluators may weigh criteria differently."])

    # -- communication --
    _add("communication", "Arguments have premises and conclusions connected by logic.",
         ["Premise: All fish live in water. Premise: A salmon is a fish. Conclusion: A salmon lives in water."],
         ["An argument can be logically valid but factually wrong."])
    _add("communication", "Analogies explain unfamiliar ideas using familiar ones.",
         ["The brain is like a computer.", "An atom is like a tiny solar system."],
         ["Analogies break down if pushed too far."])
    _add("communication", "Persuasion uses evidence, emotion, and credibility.",
         ["Cite data to persuade with evidence.", "Tell a story to persuade with emotion."],
         ["Manipulation disguises persuasion as something else."])
    _add("communication", "Irony says the opposite of what is meant.",
         ["'Great weather!' during a storm.", "'Nice job' when someone makes an obvious mistake."],
         ["Irony can be misunderstood by people who take things literally."])
    _add("communication", "Metacognition is thinking about your own thinking.",
         ["'I realize I learn better by doing than by reading.'", "'I need to slow down and re-read this carefully.'"],
         ["Being aware of bias does not automatically eliminate it."])
    _add("communication", "Nuance means a subtle difference in meaning.",
         ["'Smart' and 'clever' are similar but not identical.", "'House' and 'home' differ in emotional connotation."],
         ["Nuance is hard to convey in simple statements."])
    _add("communication", "Critical thinking evaluates information before accepting it.",
         ["Check the source of a news article.", "Ask 'Is there evidence for this claim?'"],
         ["Critical thinking takes effort and can be uncomfortable."])

    return facts


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

_STAGE_FACT_BUILDERS: dict[str, callable] = {
    "sensorimotor": _sensorimotor_facts,
    "preoperational": _preoperational_facts,
    "concrete_operational": _concrete_operational_facts,
    "formal_operational": _formal_operational_facts,
}


def get_world_seed(stage: str) -> list[WorldSeedFact]:
    """Return all World Seed facts for a specific Piaget stage.

    Parameters
    ----------
    stage : str
        Piaget stage name (sensorimotor | preoperational |
        concrete_operational | formal_operational).

    Returns
    -------
    list[WorldSeedFact]
        Curated facts for the requested stage.

    Raises
    ------
    ValueError
        If the stage is not recognized.
    """
    builder = _STAGE_FACT_BUILDERS.get(stage)
    if builder is None:
        raise ValueError(
            f"Unknown stage {stage!r}. Must be one of {list(_STAGE_FACT_BUILDERS)}"
        )
    facts = builder()
    logger.info("World seed: %d facts for stage %s", len(facts), stage)
    return facts


def get_world_seed_facts(stages: list[str] | None = None) -> dict[str, list[WorldSeedFact]]:
    """Return World Seed facts for multiple stages.

    Parameters
    ----------
    stages : list[str] | None
        Stages to include. If ``None``, returns all stages.

    Returns
    -------
    dict[str, list[WorldSeedFact]]
        Mapping from stage name to list of facts.
    """
    if stages is None:
        stages = list(STAGE_ORDER)

    result: dict[str, list[WorldSeedFact]] = {}
    for stage in stages:
        result[stage] = get_world_seed(stage)
    return result
