// Test cases for annotator skill assessment
// Each test case includes:
// - config: XML configuration for the Synapse editor
// - task: Sample data to annotate
// - groundTruth: Expected annotation result
// - difficulty: easy | medium | hard
// - points: Points awarded for correct annotation

export interface TestCase {
  id: string;
  specialty: string;
  title: string;
  description: string;
  difficulty: "easy" | "medium" | "hard";
  points: number;
  config: string;
  task: {
    data: Record<string, any>;
  };
  groundTruth: AnnotationResult[];
  scoringCriteria: ScoringCriteria;
}

export interface AnnotationResult {
  type: string;
  value: any;
  from_name: string;
  to_name: string;
}

export interface ScoringCriteria {
  type: "exact" | "overlap" | "classification" | "bbox_iou";
  threshold?: number; // For overlap/IoU scoring
  partialCredit?: boolean;
}

// ==================== COMPUTER VISION TEST CASES ====================

export const computerVisionTests: TestCase[] = [
  {
    id: "cv-001",
    specialty: "computer-vision",
    title: "Image Classification",
    description: "Classify the main subject of the image",
    difficulty: "easy",
    points: 10,
    config: `
<View>
  <Image name="image" value="$image" zoom="true"/>
  <View style="padding: 20px; margin-top: 1em; background: rgba(255,255,255,0.02); border: 1px solid #1f1f1f;">
    <Header value="What is the main subject of this image?"/>
    <Choices name="classification" toName="image" choice="single" showInLine="true">
      <Choice value="Cat"/>
      <Choice value="Dog"/>
      <Choice value="Bird"/>
      <Choice value="Other Animal"/>
    </Choices>
  </View>
</View>
    `.trim(),
    task: {
      data: {
        image: "https://upload.wikimedia.org/wikipedia/commons/thumb/3/3a/Cat03.jpg/1200px-Cat03.jpg",
      },
    },
    groundTruth: [
      {
        type: "choices",
        value: { choices: ["Cat"] },
        from_name: "classification",
        to_name: "image",
      },
    ],
    scoringCriteria: {
      type: "classification",
      partialCredit: false,
    },
  },
  {
    id: "cv-002",
    specialty: "computer-vision",
    title: "Object Detection - Bounding Box",
    description: "Draw a bounding box around the cat in the image",
    difficulty: "medium",
    points: 20,
    config: `
<View>
  <Image name="image" value="$image" zoom="true"/>
  <RectangleLabels name="label" toName="image">
    <Label value="Cat" background="#8b5cf6"/>
  </RectangleLabels>
  <View style="padding: 10px; margin-top: 1em; font-size: 14px; color: #6b7280;">
    <Header value="Instructions"/>
    <Text name="instructions" value="Draw a tight bounding box around the cat. The box should fully contain the cat without too much extra space."/>
  </View>
</View>
    `.trim(),
    task: {
      data: {
        image: "https://upload.wikimedia.org/wikipedia/commons/thumb/3/3a/Cat03.jpg/1200px-Cat03.jpg",
      },
    },
    groundTruth: [
      {
        type: "rectanglelabels",
        value: {
          x: 10,
          y: 5,
          width: 80,
          height: 90,
          rectanglelabels: ["Cat"],
        },
        from_name: "label",
        to_name: "image",
      },
    ],
    scoringCriteria: {
      type: "bbox_iou",
      threshold: 0.5, // IoU threshold for correct detection
      partialCredit: true,
    },
  },
  {
    id: "cv-003",
    specialty: "computer-vision",
    title: "Multi-class Classification",
    description: "Select all applicable attributes for this image",
    difficulty: "medium",
    points: 15,
    config: `
<View>
  <Image name="image" value="$image" zoom="true"/>
  <View style="padding: 20px; margin-top: 1em; background: rgba(255,255,255,0.02); border: 1px solid #1f1f1f;">
    <Header value="Select all attributes that apply to this image"/>
    <Choices name="attributes" toName="image" choice="multiple">
      <Choice value="Contains animal"/>
      <Choice value="Outdoor scene"/>
      <Choice value="Indoor scene"/>
      <Choice value="Natural lighting"/>
      <Choice value="Close-up shot"/>
      <Choice value="Contains text"/>
    </Choices>
  </View>
</View>
    `.trim(),
    task: {
      data: {
        image: "https://upload.wikimedia.org/wikipedia/commons/thumb/3/3a/Cat03.jpg/1200px-Cat03.jpg",
      },
    },
    groundTruth: [
      {
        type: "choices",
        value: { choices: ["Contains animal", "Indoor scene", "Close-up shot"] },
        from_name: "attributes",
        to_name: "image",
      },
    ],
    scoringCriteria: {
      type: "classification",
      partialCredit: true,
    },
  },
];

// ==================== NLP TEST CASES ====================

export const nlpTests: TestCase[] = [
  {
    id: "nlp-001",
    specialty: "natural-language-processing",
    title: "Sentiment Analysis",
    description: "Classify the sentiment of the given text",
    difficulty: "easy",
    points: 10,
    config: `
<View>
  <View style="padding: 20px; background: rgba(255,255,255,0.02); border: 1px solid #1f1f1f; margin-bottom: 1em;">
    <Text name="text" value="$text"/>
  </View>
  <View style="padding: 20px; background: rgba(139, 92, 246, 0.05); border: 1px solid rgba(139, 92, 246, 0.2);">
    <Header value="What is the sentiment of this text?"/>
    <Choices name="sentiment" toName="text" choice="single" showInLine="true">
      <Choice value="Positive"/>
      <Choice value="Negative"/>
      <Choice value="Neutral"/>
    </Choices>
  </View>
</View>
    `.trim(),
    task: {
      data: {
        text: "I absolutely loved this product! It exceeded all my expectations and I would highly recommend it to everyone.",
      },
    },
    groundTruth: [
      {
        type: "choices",
        value: { choices: ["Positive"] },
        from_name: "sentiment",
        to_name: "text",
      },
    ],
    scoringCriteria: {
      type: "classification",
      partialCredit: false,
    },
  },
  {
    id: "nlp-002",
    specialty: "natural-language-processing",
    title: "Named Entity Recognition",
    description: "Identify and label named entities in the text",
    difficulty: "medium",
    points: 25,
    config: `
<View>
  <View style="padding: 10px; margin-bottom: 1em; font-size: 14px; color: #6b7280;">
    <Header value="Instructions"/>
    <Text name="instructions" value="Select text spans and label them with the appropriate entity type: PERSON, ORGANIZATION, or LOCATION."/>
  </View>
  <Labels name="ner" toName="text">
    <Label value="PERSON" background="#8b5cf6"/>
    <Label value="ORGANIZATION" background="#3b82f6"/>
    <Label value="LOCATION" background="#22c55e"/>
  </Labels>
  <View style="padding: 20px; background: rgba(255,255,255,0.02); border: 1px solid #1f1f1f;">
    <Text name="text" value="$text"/>
  </View>
</View>
    `.trim(),
    task: {
      data: {
        text: "Elon Musk, the CEO of Tesla, announced that the company will open a new factory in Austin, Texas next year.",
      },
    },
    groundTruth: [
      {
        type: "labels",
        value: { start: 0, end: 9, text: "Elon Musk", labels: ["PERSON"] },
        from_name: "ner",
        to_name: "text",
      },
      {
        type: "labels",
        value: { start: 22, end: 27, text: "Tesla", labels: ["ORGANIZATION"] },
        from_name: "ner",
        to_name: "text",
      },
      {
        type: "labels",
        value: { start: 80, end: 86, text: "Austin", labels: ["LOCATION"] },
        from_name: "ner",
        to_name: "text",
      },
      {
        type: "labels",
        value: { start: 88, end: 93, text: "Texas", labels: ["LOCATION"] },
        from_name: "ner",
        to_name: "text",
      },
    ],
    scoringCriteria: {
      type: "overlap",
      threshold: 0.8,
      partialCredit: true,
    },
  },
  {
    id: "nlp-003",
    specialty: "natural-language-processing",
    title: "Text Classification - Topic",
    description: "Classify the topic of the article excerpt",
    difficulty: "easy",
    points: 10,
    config: `
<View>
  <View style="padding: 20px; background: rgba(255,255,255,0.02); border: 1px solid #1f1f1f; margin-bottom: 1em;">
    <Text name="text" value="$text"/>
  </View>
  <View style="padding: 20px; background: rgba(139, 92, 246, 0.05); border: 1px solid rgba(139, 92, 246, 0.2);">
    <Header value="What is the main topic of this text?"/>
    <Choices name="topic" toName="text" choice="single">
      <Choice value="Technology"/>
      <Choice value="Sports"/>
      <Choice value="Politics"/>
      <Choice value="Entertainment"/>
      <Choice value="Science"/>
      <Choice value="Health"/>
    </Choices>
  </View>
</View>
    `.trim(),
    task: {
      data: {
        text: "Scientists at CERN have discovered a new particle that could help explain the mysteries of dark matter. The research team used the Large Hadron Collider to detect the previously unknown subatomic particle.",
      },
    },
    groundTruth: [
      {
        type: "choices",
        value: { choices: ["Science"] },
        from_name: "topic",
        to_name: "text",
      },
    ],
    scoringCriteria: {
      type: "classification",
      partialCredit: false,
    },
  },
];

// ==================== AUDIO TEST CASES ====================

export const audioTests: TestCase[] = [
  {
    id: "audio-001",
    specialty: "audio-speech-processing",
    title: "Audio Classification",
    description: "Classify the type of sound in the audio clip",
    difficulty: "easy",
    points: 10,
    config: `
<View>
  <Audio name="audio" value="$audio"/>
  <View style="padding: 20px; margin-top: 1em; background: rgba(139, 92, 246, 0.05); border: 1px solid rgba(139, 92, 246, 0.2);">
    <Header value="What type of sound is this?"/>
    <Choices name="sound_type" toName="audio" choice="single">
      <Choice value="Music"/>
      <Choice value="Speech"/>
      <Choice value="Nature sounds"/>
      <Choice value="Urban noise"/>
      <Choice value="Silence"/>
    </Choices>
  </View>
</View>
    `.trim(),
    task: {
      data: {
        audio: "https://upload.wikimedia.org/wikipedia/commons/9/9d/Bach_-_Cello_Suite_no._1_in_G_major,_BWV_1007_-_I._Pr%C3%A9lude.ogg",
      },
    },
    groundTruth: [
      {
        type: "choices",
        value: { choices: ["Music"] },
        from_name: "sound_type",
        to_name: "audio",
      },
    ],
    scoringCriteria: {
      type: "classification",
      partialCredit: false,
    },
  },
  {
    id: "audio-002",
    specialty: "audio-speech-processing",
    title: "Audio Quality Rating",
    description: "Rate the quality of the audio recording",
    difficulty: "medium",
    points: 15,
    config: `
<View>
  <Audio name="audio" value="$audio"/>
  <View style="padding: 20px; margin-top: 1em; background: rgba(255,255,255,0.02); border: 1px solid #1f1f1f;">
    <Header value="Rate the following aspects of the audio"/>
    <View style="margin-top: 1em;">
      <Header value="Audio Clarity" size="5"/>
      <Rating name="clarity" toName="audio" maxRating="5"/>
    </View>
    <View style="margin-top: 1em;">
      <Header value="Background Noise Level (5 = No noise)" size="5"/>
      <Rating name="noise" toName="audio" maxRating="5"/>
    </View>
  </View>
</View>
    `.trim(),
    task: {
      data: {
        audio: "https://upload.wikimedia.org/wikipedia/commons/9/9d/Bach_-_Cello_Suite_no._1_in_G_major,_BWV_1007_-_I._Pr%C3%A9lude.ogg",
      },
    },
    groundTruth: [
      {
        type: "rating",
        value: { rating: 5 },
        from_name: "clarity",
        to_name: "audio",
      },
      {
        type: "rating",
        value: { rating: 5 },
        from_name: "noise",
        to_name: "audio",
      },
    ],
    scoringCriteria: {
      type: "exact",
      partialCredit: true,
    },
  },
];

// ==================== CONVERSATIONAL AI TEST CASES ====================

export const conversationalAITests: TestCase[] = [
  {
    id: "conv-001",
    specialty: "conversational-ai",
    title: "Intent Classification",
    description: "Classify the user's intent in the conversation",
    difficulty: "easy",
    points: 10,
    config: `
<View>
  <View style="padding: 20px; background: rgba(255,255,255,0.02); border: 1px solid #1f1f1f; margin-bottom: 1em;">
    <Header value="User Message"/>
    <Text name="message" value="$message"/>
  </View>
  <View style="padding: 20px; background: rgba(139, 92, 246, 0.05); border: 1px solid rgba(139, 92, 246, 0.2);">
    <Header value="What is the user's intent?"/>
    <Choices name="intent" toName="message" choice="single">
      <Choice value="Question"/>
      <Choice value="Complaint"/>
      <Choice value="Request"/>
      <Choice value="Greeting"/>
      <Choice value="Feedback"/>
      <Choice value="Other"/>
    </Choices>
  </View>
</View>
    `.trim(),
    task: {
      data: {
        message: "Hi, I'd like to cancel my subscription and get a refund for the remaining months. This service hasn't been working properly for weeks.",
      },
    },
    groundTruth: [
      {
        type: "choices",
        value: { choices: ["Request"] },
        from_name: "intent",
        to_name: "message",
      },
    ],
    scoringCriteria: {
      type: "classification",
      partialCredit: false,
    },
  },
  {
    id: "conv-002",
    specialty: "conversational-ai",
    title: "Response Quality Evaluation",
    description: "Evaluate the quality of an AI assistant's response",
    difficulty: "medium",
    points: 20,
    config: `
<View>
  <View style="padding: 20px; background: rgba(255,255,255,0.02); border: 1px solid #1f1f1f; margin-bottom: 1em;">
    <Header value="User Question"/>
    <Text name="question" value="$question"/>
  </View>
  <View style="padding: 20px; background: rgba(59, 130, 246, 0.05); border: 1px solid rgba(59, 130, 246, 0.2); margin-bottom: 1em;">
    <Header value="AI Response"/>
    <Text name="response" value="$response"/>
  </View>
  <View style="padding: 20px; background: rgba(139, 92, 246, 0.05); border: 1px solid rgba(139, 92, 246, 0.2);">
    <Header value="Rate the response quality"/>
    <View style="margin-top: 1em;">
      <Header value="Relevance (1-5)" size="5"/>
      <Rating name="relevance" toName="response" maxRating="5"/>
    </View>
    <View style="margin-top: 1em;">
      <Header value="Helpfulness (1-5)" size="5"/>
      <Rating name="helpfulness" toName="response" maxRating="5"/>
    </View>
    <View style="margin-top: 1em;">
      <Header value="Accuracy (1-5)" size="5"/>
      <Rating name="accuracy" toName="response" maxRating="5"/>
    </View>
  </View>
</View>
    `.trim(),
    task: {
      data: {
        question: "What is the capital of France?",
        response: "The capital of France is Paris. Paris is located in the north-central part of France and is the country's largest city with a population of over 2 million people in the city proper.",
      },
    },
    groundTruth: [
      {
        type: "rating",
        value: { rating: 5 },
        from_name: "relevance",
        to_name: "response",
      },
      {
        type: "rating",
        value: { rating: 5 },
        from_name: "helpfulness",
        to_name: "response",
      },
      {
        type: "rating",
        value: { rating: 5 },
        from_name: "accuracy",
        to_name: "response",
      },
    ],
    scoringCriteria: {
      type: "exact",
      partialCredit: true,
    },
  },
];

// ==================== GENERATIVE AI TEST CASES ====================

export const generativeAITests: TestCase[] = [
  {
    id: "gen-001",
    specialty: "generative-ai",
    title: "Response Comparison",
    description: "Compare two AI-generated responses and select the better one",
    difficulty: "medium",
    points: 15,
    config: `
<View>
  <View style="padding: 20px; background: rgba(255,255,255,0.02); border: 1px solid #1f1f1f; margin-bottom: 1em;">
    <Header value="User Prompt"/>
    <Text name="prompt" value="$prompt"/>
  </View>
  <View style="display: grid; grid-template-columns: 1fr 1fr; gap: 1em; margin-bottom: 1em;">
    <View style="padding: 20px; background: rgba(139, 92, 246, 0.05); border: 1px solid rgba(139, 92, 246, 0.2);">
      <Header value="Response A"/>
      <Text name="response_a" value="$response_a"/>
    </View>
    <View style="padding: 20px; background: rgba(59, 130, 246, 0.05); border: 1px solid rgba(59, 130, 246, 0.2);">
      <Header value="Response B"/>
      <Text name="response_b" value="$response_b"/>
    </View>
  </View>
  <View style="padding: 20px; background: rgba(255,255,255,0.02); border: 1px solid #1f1f1f;">
    <Header value="Which response is better overall?"/>
    <Choices name="preference" toName="prompt" choice="single" showInLine="true">
      <Choice value="Response A is much better"/>
      <Choice value="Response A is slightly better"/>
      <Choice value="About the same"/>
      <Choice value="Response B is slightly better"/>
      <Choice value="Response B is much better"/>
    </Choices>
  </View>
</View>
    `.trim(),
    task: {
      data: {
        prompt: "Explain quantum computing in simple terms.",
        response_a: "Quantum computing is like having a super-powered calculator that can explore many possibilities at once. While regular computers use bits (0s and 1s), quantum computers use qubits that can be both 0 and 1 simultaneously, allowing them to solve certain complex problems much faster.",
        response_b: "Quantum computing utilizes quantum mechanical phenomena such as superposition and entanglement to perform computational operations on quantum bits or qubits, enabling exponential speedup for specific algorithmic classes including Shor's factoring algorithm.",
      },
    },
    groundTruth: [
      {
        type: "choices",
        value: { choices: ["Response A is much better"] },
        from_name: "preference",
        to_name: "prompt",
      },
    ],
    scoringCriteria: {
      type: "classification",
      partialCredit: true,
    },
  },
  {
    id: "gen-002",
    specialty: "generative-ai",
    title: "Content Safety Check",
    description: "Evaluate if the AI response is safe and appropriate",
    difficulty: "easy",
    points: 10,
    config: `
<View>
  <View style="padding: 20px; background: rgba(255,255,255,0.02); border: 1px solid #1f1f1f; margin-bottom: 1em;">
    <Header value="AI Generated Response"/>
    <Text name="response" value="$response"/>
  </View>
  <View style="padding: 20px; background: rgba(139, 92, 246, 0.05); border: 1px solid rgba(139, 92, 246, 0.2);">
    <Header value="Is this response safe and appropriate?"/>
    <Choices name="safety" toName="response" choice="single" showInLine="true">
      <Choice value="Safe"/>
      <Choice value="Potentially Harmful"/>
      <Choice value="Harmful"/>
    </Choices>
    <View style="margin-top: 1em;">
      <Header value="Select any issues present (if any)" size="5"/>
      <Choices name="issues" toName="response" choice="multiple">
        <Choice value="Contains misinformation"/>
        <Choice value="Biased content"/>
        <Choice value="Offensive language"/>
        <Choice value="Privacy concerns"/>
        <Choice value="No issues"/>
      </Choices>
    </View>
  </View>
</View>
    `.trim(),
    task: {
      data: {
        response: "Here's a simple recipe for chocolate chip cookies: Mix 2 cups flour, 1 cup sugar, 1 cup butter, 2 eggs, 1 tsp vanilla, 1 tsp baking soda, and 2 cups chocolate chips. Bake at 375°F for 10-12 minutes. Enjoy!",
      },
    },
    groundTruth: [
      {
        type: "choices",
        value: { choices: ["Safe"] },
        from_name: "safety",
        to_name: "response",
      },
      {
        type: "choices",
        value: { choices: ["No issues"] },
        from_name: "issues",
        to_name: "response",
      },
    ],
    scoringCriteria: {
      type: "classification",
      partialCredit: true,
    },
  },
];

// ==================== RANKING TEST CASES ====================

export const rankingTests: TestCase[] = [
  {
    id: "rank-001",
    specialty: "ranking-and-scoring",
    title: "Search Result Relevance",
    description: "Rate the relevance of search results to a query",
    difficulty: "easy",
    points: 15,
    config: `
<View>
  <View style="padding: 20px; background: rgba(139, 92, 246, 0.1); border: 1px solid rgba(139, 92, 246, 0.3); margin-bottom: 1em;">
    <Header value="Search Query"/>
    <Text name="query" value="$query"/>
  </View>
  <View style="padding: 20px; background: rgba(255,255,255,0.02); border: 1px solid #1f1f1f;">
    <Header value="Search Result"/>
    <Text name="result" value="$result"/>
  </View>
  <View style="padding: 20px; margin-top: 1em; background: rgba(255,255,255,0.02); border: 1px solid #1f1f1f;">
    <Header value="How relevant is this result to the query?"/>
    <Choices name="relevance" toName="result" choice="single" showInLine="true">
      <Choice value="Highly Relevant"/>
      <Choice value="Somewhat Relevant"/>
      <Choice value="Marginally Relevant"/>
      <Choice value="Not Relevant"/>
    </Choices>
  </View>
</View>
    `.trim(),
    task: {
      data: {
        query: "best Italian restaurants in New York",
        result: "Tony's Pizza - Authentic Italian cuisine in the heart of Manhattan. Award-winning pasta dishes and wood-fired pizzas. Open daily for lunch and dinner.",
      },
    },
    groundTruth: [
      {
        type: "choices",
        value: { choices: ["Highly Relevant"] },
        from_name: "relevance",
        to_name: "result",
      },
    ],
    scoringCriteria: {
      type: "classification",
      partialCredit: true,
    },
  },
  {
    id: "rank-002",
    specialty: "ranking-and-scoring",
    title: "Content Quality Rating",
    description: "Rate the overall quality of user-generated content",
    difficulty: "medium",
    points: 20,
    config: `
<View>
  <View style="padding: 20px; background: rgba(255,255,255,0.02); border: 1px solid #1f1f1f; margin-bottom: 1em;">
    <Header value="Product Review"/>
    <Text name="review" value="$review"/>
  </View>
  <View style="padding: 20px; background: rgba(139, 92, 246, 0.05); border: 1px solid rgba(139, 92, 246, 0.2);">
    <Header value="Rate the quality of this review"/>
    <View style="margin-top: 1em;">
      <Header value="Informativeness (1-5)" size="5"/>
      <Rating name="informativeness" toName="review" maxRating="5"/>
    </View>
    <View style="margin-top: 1em;">
      <Header value="Clarity (1-5)" size="5"/>
      <Rating name="clarity" toName="review" maxRating="5"/>
    </View>
    <View style="margin-top: 1em;">
      <Header value="Usefulness (1-5)" size="5"/>
      <Rating name="usefulness" toName="review" maxRating="5"/>
    </View>
  </View>
</View>
    `.trim(),
    task: {
      data: {
        review: "Great product! I've been using this laptop for 3 months now. The battery life is excellent (8+ hours), the screen is crisp, and it handles my video editing software without any issues. Only downside is the fan can be a bit loud under heavy load. Would recommend for creative professionals.",
      },
    },
    groundTruth: [
      {
        type: "rating",
        value: { rating: 5 },
        from_name: "informativeness",
        to_name: "review",
      },
      {
        type: "rating",
        value: { rating: 5 },
        from_name: "clarity",
        to_name: "review",
      },
      {
        type: "rating",
        value: { rating: 5 },
        from_name: "usefulness",
        to_name: "review",
      },
    ],
    scoringCriteria: {
      type: "exact",
      partialCredit: true,
    },
  },
];

// ==================== TEST CASES REGISTRY ====================

export const ALL_TEST_CASES: Record<string, TestCase[]> = {
  "computer-vision": computerVisionTests,
  "natural-language-processing": nlpTests,
  "audio-speech-processing": audioTests,
  "conversational-ai": conversationalAITests,
  "generative-ai": generativeAITests,
  "ranking-and-scoring": rankingTests,
};

export const getTestCasesForSpecialties = (specialtyIds: string[]): TestCase[] => {
  const testCases: TestCase[] = [];
  
  for (const id of specialtyIds) {
    const cases = ALL_TEST_CASES[id];
    if (cases) {
      testCases.push(...cases);
    }
  }
  
  return testCases;
};

export const getTotalPoints = (testCases: TestCase[]): number => {
  return testCases.reduce((total, tc) => total + tc.points, 0);
};

export const getEstimatedTime = (testCases: TestCase[]): number => {
  // Estimate ~2 min for easy, ~3 min for medium, ~5 min for hard
  const timePerDifficulty = { easy: 2, medium: 3, hard: 5 };
  return testCases.reduce((total, tc) => total + timePerDifficulty[tc.difficulty], 0);
};
