import { AudioView, Synapse } from "@synapse/frontend-test/helpers/SF";

describe("Audio", () => {
  it("Renders audio with merged channels by default", () => {
    Synapse.params()
      .config(
        `
      <View>
        <Audio name="audio" value="$audio" />
      </View>
      `,
      )
      .data({
        audio: "/public/files/barradeen-emotional.mp3",
      })
      .withResult([])
      .init();

    Synapse.waitForObjectsReady();

    AudioView.isReady();
    AudioView.toMatchImageSnapshot(AudioView.drawingArea, { threshold: 0.4 });
  });

  it("Renders separate audio channels with splitchannels=true", () => {
    Synapse.params()
      .config(
        `
      <View>
        <Audio name="audio" value="$audio" splitchannels="true" />
      </View>
      `,
      )
      .data({
        audio: "/public/files/barradeen-emotional.mp3",
      })
      .withResult([])
      .init();

    Synapse.waitForObjectsReady();

    AudioView.isReady();
    AudioView.toMatchImageSnapshot(AudioView.drawingArea, { threshold: 0.4 });
  });
});

