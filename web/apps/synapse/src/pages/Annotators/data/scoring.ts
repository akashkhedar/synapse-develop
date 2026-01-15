import type { TestCase, AnnotationResult, ScoringCriteria } from "./testCases";

export interface TaskScore {
  testCaseId: string;
  specialty: string;
  title: string;
  maxPoints: number;
  earnedPoints: number;
  percentage: number;
  feedback: string;
  details: ScoreDetail[];
}

export interface ScoreDetail {
  annotation: string;
  expected: string;
  match: boolean;
  partialScore?: number;
}

export interface TestResult {
  totalPoints: number;
  earnedPoints: number;
  percentage: number;
  passed: boolean;
  passingThreshold: number;
  taskScores: TaskScore[];
  specialtyScores: Record<string, SpecialtyScore>;
  timeTaken: number; // in seconds
}

export interface SpecialtyScore {
  specialty: string;
  totalPoints: number;
  earnedPoints: number;
  percentage: number;
  taskCount: number;
  passed: boolean;
}

const PASSING_THRESHOLD = 70; // 70% to pass

/**
 * Calculate IoU (Intersection over Union) for bounding boxes
 */
function calculateIoU(
  box1: { x: number; y: number; width: number; height: number },
  box2: { x: number; y: number; width: number; height: number }
): number {
  const x1 = Math.max(box1.x, box2.x);
  const y1 = Math.max(box1.y, box2.y);
  const x2 = Math.min(box1.x + box1.width, box2.x + box2.width);
  const y2 = Math.min(box1.y + box1.height, box2.y + box2.height);

  const intersectionArea = Math.max(0, x2 - x1) * Math.max(0, y2 - y1);
  const box1Area = box1.width * box1.height;
  const box2Area = box2.width * box2.height;
  const unionArea = box1Area + box2Area - intersectionArea;

  return unionArea > 0 ? intersectionArea / unionArea : 0;
}

/**
 * Calculate text overlap score for NER-style annotations
 */
function calculateTextOverlap(
  annotation: { start: number; end: number },
  groundTruth: { start: number; end: number }
): number {
  const overlapStart = Math.max(annotation.start, groundTruth.start);
  const overlapEnd = Math.min(annotation.end, groundTruth.end);
  const overlap = Math.max(0, overlapEnd - overlapStart);

  const annotationLength = annotation.end - annotation.start;
  const groundTruthLength = groundTruth.end - groundTruth.start;
  const unionLength = annotationLength + groundTruthLength - overlap;

  return unionLength > 0 ? overlap / unionLength : 0;
}

/**
 * Score a classification annotation (choices)
 */
function scoreClassification(
  userAnnotation: AnnotationResult | undefined,
  groundTruth: AnnotationResult,
  criteria: ScoringCriteria
): { score: number; feedback: string; details: ScoreDetail[] } {
  const details: ScoreDetail[] = [];

  if (!userAnnotation) {
    return {
      score: 0,
      feedback: "No answer provided",
      details: [
        {
          annotation: "None",
          expected: JSON.stringify(groundTruth.value.choices),
          match: false,
        },
      ],
    };
  }

  const userChoices = userAnnotation.value?.choices || [];
  const expectedChoices = groundTruth.value?.choices || [];

  // Check for exact match
  const userSet = new Set(userChoices);
  const expectedSet = new Set(expectedChoices);

  const intersection = [...userSet].filter((x) => expectedSet.has(x));
  const union = new Set([...userSet, ...expectedSet]);

  details.push({
    annotation: userChoices.join(", "),
    expected: expectedChoices.join(", "),
    match:
      intersection.length === expectedSet.size &&
      userSet.size === expectedSet.size,
  });

  if (criteria.partialCredit && union.size > 0) {
    // Partial credit based on correct choices
    const score = intersection.length / expectedSet.size;
    // Penalty for extra wrong choices
    const penalty =
      (userSet.size - intersection.length) / Math.max(expectedSet.size, 1);
    const finalScore = Math.max(0, score - penalty * 0.5);

    return {
      score: finalScore,
      feedback:
        finalScore === 1
          ? "Correct!"
          : `Partially correct (${(finalScore * 100).toFixed(0)}%)`,
      details,
    };
  }

  // Exact match only
  const isCorrect =
    intersection.length === expectedSet.size &&
    userSet.size === expectedSet.size;
  return {
    score: isCorrect ? 1 : 0,
    feedback: isCorrect ? "Correct!" : "Incorrect",
    details,
  };
}

/**
 * Score a rating annotation
 */
function scoreRating(
  userAnnotation: AnnotationResult | undefined,
  groundTruth: AnnotationResult,
  criteria: ScoringCriteria
): { score: number; feedback: string; details: ScoreDetail[] } {
  const details: ScoreDetail[] = [];

  if (!userAnnotation) {
    return {
      score: 0,
      feedback: "No rating provided",
      details: [
        {
          annotation: "None",
          expected: String(groundTruth.value.rating),
          match: false,
        },
      ],
    };
  }

  const userRating = userAnnotation.value?.rating;
  const expectedRating = groundTruth.value?.rating;

  if (userRating === undefined || expectedRating === undefined) {
    return { score: 0, feedback: "Invalid rating", details };
  }

  const difference = Math.abs(userRating - expectedRating);
  const maxDiff = 4; // Assuming 5-point scale

  details.push({
    annotation: String(userRating),
    expected: String(expectedRating),
    match: difference === 0,
    partialScore: criteria.partialCredit
      ? Math.max(0, 1 - difference / maxDiff)
      : difference === 0
      ? 1
      : 0,
  });

  if (criteria.partialCredit) {
    const score = Math.max(0, 1 - difference / maxDiff);
    return {
      score,
      feedback:
        difference === 0 ? "Exact match!" : `Close (off by ${difference})`,
      details,
    };
  }

  return {
    score: difference === 0 ? 1 : 0,
    feedback: difference === 0 ? "Correct!" : "Incorrect",
    details,
  };
}

/**
 * Score a bounding box annotation
 */
function scoreBoundingBox(
  userAnnotations: AnnotationResult[],
  groundTruth: AnnotationResult[],
  criteria: ScoringCriteria
): { score: number; feedback: string; details: ScoreDetail[] } {
  const details: ScoreDetail[] = [];
  const threshold = criteria.threshold || 0.5;

  if (userAnnotations.length === 0) {
    return {
      score: 0,
      feedback: "No bounding boxes drawn",
      details: [
        {
          annotation: "None",
          expected: `${groundTruth.length} box(es)`,
          match: false,
        },
      ],
    };
  }

  let matchedCount = 0;
  let totalIoU = 0;

  for (const gt of groundTruth) {
    const gtBox = gt.value;
    let bestIoU = 0;
    let bestMatch: AnnotationResult | null = null;

    for (const user of userAnnotations) {
      if (user.type !== gt.type) continue;

      const userBox = user.value;
      // Check if labels match
      const gtLabels = gtBox.rectanglelabels || [];
      const userLabels = userBox.rectanglelabels || [];

      if (!gtLabels.some((l: string) => userLabels.includes(l))) continue;

      const iou = calculateIoU(userBox, gtBox);
      if (iou > bestIoU) {
        bestIoU = iou;
        bestMatch = user;
      }
    }

    details.push({
      annotation: bestMatch
        ? `IoU: ${(bestIoU * 100).toFixed(1)}%`
        : "No match",
      expected: gtBox.rectanglelabels?.join(", ") || "Box",
      match: bestIoU >= threshold,
      partialScore: bestIoU,
    });

    if (bestIoU >= threshold) {
      matchedCount++;
    }
    totalIoU += bestIoU;
  }

  const avgIoU = groundTruth.length > 0 ? totalIoU / groundTruth.length : 0;
  const matchRatio =
    groundTruth.length > 0 ? matchedCount / groundTruth.length : 0;

  if (criteria.partialCredit) {
    return {
      score: avgIoU,
      feedback:
        matchedCount === groundTruth.length
          ? `All boxes matched (avg IoU: ${(avgIoU * 100).toFixed(0)}%)`
          : `${matchedCount}/${groundTruth.length} boxes matched`,
      details,
    };
  }

  return {
    score: matchRatio,
    feedback:
      matchedCount === groundTruth.length
        ? "All boxes correct!"
        : `${matchedCount}/${groundTruth.length} correct`,
    details,
  };
}

/**
 * Score text span annotations (NER, labels)
 */
function scoreTextSpans(
  userAnnotations: AnnotationResult[],
  groundTruth: AnnotationResult[],
  criteria: ScoringCriteria
): { score: number; feedback: string; details: ScoreDetail[] } {
  const details: ScoreDetail[] = [];
  const threshold = criteria.threshold || 0.8;

  if (userAnnotations.length === 0 && groundTruth.length > 0) {
    return {
      score: 0,
      feedback: "No annotations provided",
      details: [
        {
          annotation: "None",
          expected: `${groundTruth.length} entity/entities`,
          match: false,
        },
      ],
    };
  }

  let matchedCount = 0;
  let totalScore = 0;

  for (const gt of groundTruth) {
    let bestOverlap = 0;
    let bestMatch: AnnotationResult | null = null;

    for (const user of userAnnotations) {
      if (user.type !== gt.type) continue;

      // Check label match
      const gtLabels = gt.value.labels || [];
      const userLabels = user.value.labels || [];
      if (!gtLabels.some((l: string) => userLabels.includes(l))) continue;

      const overlap = calculateTextOverlap(
        { start: user.value.start, end: user.value.end },
        { start: gt.value.start, end: gt.value.end }
      );

      if (overlap > bestOverlap) {
        bestOverlap = overlap;
        bestMatch = user;
      }
    }

    details.push({
      annotation: bestMatch
        ? `"${bestMatch.value.text}" (${(bestOverlap * 100).toFixed(
            0
          )}% overlap)`
        : "No match",
      expected: `"${gt.value.text}" [${gt.value.labels?.join(", ")}]`,
      match: bestOverlap >= threshold,
      partialScore: bestOverlap,
    });

    if (bestOverlap >= threshold) {
      matchedCount++;
    }
    totalScore += bestOverlap;
  }

  // Penalty for extra annotations
  const extraCount = Math.max(0, userAnnotations.length - groundTruth.length);
  const penalty = extraCount * 0.1;

  const avgScore = groundTruth.length > 0 ? totalScore / groundTruth.length : 0;
  const finalScore = criteria.partialCredit
    ? Math.max(0, avgScore - penalty)
    : matchedCount / Math.max(groundTruth.length, 1);

  return {
    score: finalScore,
    feedback:
      matchedCount === groundTruth.length
        ? "All entities correctly identified!"
        : `${matchedCount}/${groundTruth.length} entities matched`,
    details,
  };
}

/**
 * Score a single test case
 */
export function scoreTestCase(
  testCase: TestCase,
  userAnnotations: AnnotationResult[]
): TaskScore {
  const { scoringCriteria, groundTruth, points: maxPoints } = testCase;

  let totalScore = 0;
  let feedbackParts: string[] = [];
  let allDetails: ScoreDetail[] = [];

  // Group annotations by type/from_name for matching
  const userByFromName = new Map<string, AnnotationResult[]>();
  for (const ann of userAnnotations) {
    const key = ann.from_name;
    if (!userByFromName.has(key)) {
      userByFromName.set(key, []);
    }
    userByFromName.get(key)!.push(ann);
  }

  const gtByFromName = new Map<string, AnnotationResult[]>();
  for (const ann of groundTruth) {
    const key = ann.from_name;
    if (!gtByFromName.has(key)) {
      gtByFromName.set(key, []);
    }
    gtByFromName.get(key)!.push(ann);
  }

  // Score each from_name group
  for (const [fromName, gtAnns] of gtByFromName) {
    let userAnns = userByFromName.get(fromName) || [];

    // Fallback: If no exact match, try to match by type
    if (userAnns.length === 0 && userAnnotations.length > 0) {
      // Find any user annotation that has the same type as the ground truth
      const firstGt = gtAnns[0];
      const matchByType = userAnnotations.find(
        (ua) => ua.type === firstGt.type
      );
      if (matchByType) {
        userAnns = [matchByType];
      }
    }

    const firstGt = gtAnns[0];
    let result: { score: number; feedback: string; details: ScoreDetail[] };

    switch (scoringCriteria.type) {
      case "classification":
        result = scoreClassification(userAnns[0], firstGt, scoringCriteria);
        break;
      case "exact":
        // For ratings and exact matches
        if (firstGt.type === "rating") {
          result = scoreRating(userAnns[0], firstGt, scoringCriteria);
        } else {
          result = scoreClassification(userAnns[0], firstGt, scoringCriteria);
        }
        break;
      case "bbox_iou":
        result = scoreBoundingBox(userAnns, gtAnns, scoringCriteria);
        break;
      case "overlap":
        result = scoreTextSpans(userAnns, gtAnns, scoringCriteria);
        break;
      default:
        result = scoreClassification(userAnns[0], firstGt, scoringCriteria);
    }

    if (userAnns.length === 0 && userAnnotations.length > 0) {
      // Debug info if we still found nothing but user DID provide answers
      const foundNames = Array.from(userByFromName.keys()).join(", ");
      result.feedback += ` (Internal: Expected '${fromName}', found [${foundNames}])`;
    }

    totalScore += result.score;
    feedbackParts.push(result.feedback);
    allDetails.push(...result.details);
  }

  // Average score across all from_names
  const avgScore = gtByFromName.size > 0 ? totalScore / gtByFromName.size : 0;
  const earnedPoints = Math.round(avgScore * maxPoints * 10) / 10;

  return {
    testCaseId: testCase.id,
    specialty: testCase.specialty,
    title: testCase.title,
    maxPoints,
    earnedPoints,
    percentage: avgScore * 100,
    feedback: feedbackParts.join("; "),
    details: allDetails,
  };
}

/**
 * Calculate overall test results
 */
export function calculateTestResults(
  testCases: TestCase[],
  userAnswers: Map<string, AnnotationResult[]>,
  timeTaken: number
): TestResult {
  const taskScores: TaskScore[] = [];
  const specialtyTotals: Record<
    string,
    { total: number; earned: number; count: number }
  > = {};

  let totalPoints = 0;
  let earnedPoints = 0;

  for (const testCase of testCases) {
    const userAnnotations = userAnswers.get(testCase.id) || [];
    const score = scoreTestCase(testCase, userAnnotations);
    taskScores.push(score);

    totalPoints += score.maxPoints;
    earnedPoints += score.earnedPoints;

    // Aggregate by specialty
    if (!specialtyTotals[testCase.specialty]) {
      specialtyTotals[testCase.specialty] = { total: 0, earned: 0, count: 0 };
    }
    specialtyTotals[testCase.specialty].total += score.maxPoints;
    specialtyTotals[testCase.specialty].earned += score.earnedPoints;
    specialtyTotals[testCase.specialty].count++;
  }

  // Calculate specialty scores
  const specialtyScores: Record<string, SpecialtyScore> = {};
  for (const [specialty, data] of Object.entries(specialtyTotals)) {
    const percentage = data.total > 0 ? (data.earned / data.total) * 100 : 0;
    specialtyScores[specialty] = {
      specialty,
      totalPoints: data.total,
      earnedPoints: data.earned,
      percentage,
      taskCount: data.count,
      passed: percentage >= PASSING_THRESHOLD,
    };
  }

  const overallPercentage =
    totalPoints > 0 ? (earnedPoints / totalPoints) * 100 : 0;

  return {
    totalPoints,
    earnedPoints: Math.round(earnedPoints * 10) / 10,
    percentage: Math.round(overallPercentage * 10) / 10,
    passed: overallPercentage >= PASSING_THRESHOLD,
    passingThreshold: PASSING_THRESHOLD,
    taskScores,
    specialtyScores,
    timeTaken,
  };
}
