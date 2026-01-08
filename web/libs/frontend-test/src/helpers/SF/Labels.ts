export const Labels = {
  get root() {
    return cy.get(".sf-labels");
  },
  get labels() {
    return this.root;
  },
  get label() {
    return this.labels.get(".sf-label");
  },
  get selectedLabel() {
    return this.label.filter(".sf-label_selected");
  },
  select(labelName: string) {
    this.label.contains(labelName).click();
    this.selectedLabel.should("be.visible").should("have.length.gt", 0);
  },
  selectWithHotkey(hotkey: string) {
    cy.get("body").type(`${hotkey}`);
    this.selectedLabel.contains(`${hotkey}`).should("be.visible").should("have.length.gt", 0);
  },
};

