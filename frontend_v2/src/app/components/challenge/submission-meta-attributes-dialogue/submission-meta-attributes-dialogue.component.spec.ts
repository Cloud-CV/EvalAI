import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { SubmissionMetaAttributesDialogueComponent } from './submission-meta-attributes-dialogue.component';

describe('SubmissionMetaAttributesDialogueComponent', () => {
  let component: SubmissionMetaAttributesDialogueComponent;
  let fixture: ComponentFixture<SubmissionMetaAttributesDialogueComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ SubmissionMetaAttributesDialogueComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(SubmissionMetaAttributesDialogueComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
