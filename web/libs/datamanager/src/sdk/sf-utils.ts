import type {
  APIAnnotation,
  APIPrediction,
  APITask,
  sfAnnotation,
  sfTaskData,
} from "../types/Task";

/**
 * Converts the task from the server format to the
 * format supported by the LS frontend
 * @param {import("../stores/Tasks").TaskModel} task
 * @private
 */
export const taskToSFFormat = (task: APITask): sfTaskData | void => {
  if (!task) return;

  const result: sfTaskData = {
    ...task,
    annotations: [],
    predictions: [],
    createdAt: task.created_at,
    // isLabeled: task.is_labeled, // @todo why?
  };

  if (task.annotations) {
    result.annotations = task.annotations.map(annotationTosf);
  }

  if (task.predictions) {
    result.predictions = task.predictions.map(predictionTosf);
  }

  return result;
};

export const annotationTosf = (annotation: APIAnnotation) => {
  const createdDate = annotation.draft_created_at || annotation.created_at;

  return {
    ...annotation,
    id: undefined,
    pk: String(annotation.id),
    createdAgo: annotation.created_ago,
    createdBy: annotation.created_username,
    createdDate,
    leadTime: annotation.lead_time ?? 0,
    skipped: annotation.was_cancelled ?? false,
  };
};

export const predictionTosf = (prediction: APIPrediction) => {
  return {
    ...prediction,
    id: undefined,
    pk: String(prediction.id),
    createdAgo: prediction.created_ago,
    createdBy: prediction.model_version?.trim() ?? "",
    createdDate: prediction.created_at,
  };
};

export const annotationToServer = (annotation: sfAnnotation): APIAnnotation => {
  return {
    ...annotation,
    id: Number(annotation.pk),
    created_ago: annotation.createdAgo,
    created_username: annotation.createdBy,
    created_at: new Date().toISOString(),
    lead_time: annotation.leadTime,
  };
};

export const getAnnotationSnapshot = (c: sfAnnotation) => ({
  id: c.id,
  pk: c.pk,
  result: c.serializeAnnotation(),
  leadTime: c.leadTime,
  userGenerate: !!c.userGenerate,
  sentUserGenerate: !!c.sentUserGenerate,
});
