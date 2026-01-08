import { AudioView, Synapse } from "@synapse/frontend-test/helpers/SF";
import {
  audioErrorsConfig,
  audioDecoderErrorData,
  audioHttpErrorData,
  audioErrorsAnnotations,
} from "../../data/audio/audio_errors";

describe("Audio Errors", () => {
  beforeEach(() => {
    Synapse.setFeatureFlagsOnPageLoad({
      ff_front_dev_2715_audio_3_280722_short: true,
    });
  });

  it("Check if audio decoder error handler is showing", () => {
    Synapse.params()
      .config(audioErrorsConfig)
      .data(audioDecoderErrorData)
      .withResult(audioErrorsAnnotations)
      .init();

    Synapse.waitForObjectsReady();

    // Check for the error message using the helper method
    AudioView.hasError("An error occurred while decoding the audio file");
  });

  it("Check if audio http error handler is showing", () => {
    Synapse.params().config(audioErrorsConfig).data(audioHttpErrorData).withResult(audioErrorsAnnotations).init();

    Synapse.waitForObjectsReady();

    // Check for the HTTP error message using the helper method
    AudioView.hasError("HTTP error status: 404");
  });
});

