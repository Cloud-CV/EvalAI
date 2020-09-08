import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { ChallengeanalyticsComponent } from './challengeanalytics.component';

describe('ChallengeanalyticsComponent', () => {
  let component: ChallengeanalyticsComponent;
  let fixture: ComponentFixture<ChallengeanalyticsComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ChallengeanalyticsComponent],
    }).compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(ChallengeanalyticsComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
