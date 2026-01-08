export const Relations = {
  get relations() {
    return cy.get(".sf-relations");
  },
  get relationOrderList() {
    const relationList = [];

    cy.get(".sf-relations__item").each(($el) => {
      const from = $el.find(".sf-detailed-region .sf-labels-list span").first().text().trim();
      const to = $el.find(".sf-detailed-region .sf-labels-list span").last().text().trim();
      relationList.push({ from, to });
    });

    return cy.wrap(relationList);
  },
  get relationItems() {
    return this.relations.find(".sf-relations__item");
  },
  get relationRegions() {
    return this.relationItems.find(".sf-detailed-region");
  },
  get hideAllRelationsButton() {
    return cy.get('[aria-label="Hide all"]');
  },
  get showAllRelationsButton() {
    return cy.get('[aria-label="Show all"]');
  },
  get ascendingOrderRelationButton() {
    return cy.get('[aria-label="Order by oldest"]');
  },
  get descendingOrderRelationButton() {
    return cy.get('[aria-label="Order by newest"]');
  },
  get hiddenRelations() {
    return this.relations.should("be.visible").get(".sf-relations__item_hidden .sf-relations__content");
  },
  get overlay() {
    return cy.get(".relations-overlay");
  },
  get overlayItems() {
    return this.overlay.find("g");
  },
  hasRelations(count: number) {
    cy.get(".sf-details__section-head")
      .filter((index, element) => Cypress.$(element).next(".sf-relation-controls").length > 0)
      .should("have.text", `Relations (${count})`);
  },
  hasRelation(from: string, to: string) {
    cy.get(".sf-relations").contains(from).closest(".sf-relations").contains(to);
  },
  hasHiddenRelations(count: number) {
    this.hiddenRelations.should("have.length", count);
  },
  toggleCreation() {
    cy.get('button[aria-label="Create Relation"]').click();
  },
  toggleCreationWithHotkey() {
    // hotkey is alt + r
    cy.get("body").type("{alt}r");
  },
  toggleRelationVisibility(idx) {
    cy.get(".sf-relations__item")
      .eq(idx)
      .trigger("mouseover")
      .find(".sf-relations__actions")
      .find('button[aria-label="Hide Relation"]')
      .click({ force: true });
  },
};

