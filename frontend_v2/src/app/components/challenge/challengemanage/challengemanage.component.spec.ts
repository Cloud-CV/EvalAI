import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { ChallengemanageComponent } from './challengemanage.component';

describe('ChallengemanageComponent', () => {
  let component: ChallengemanageComponent;
  let fixture: ComponentFixture<ChallengemanageComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ChallengemanageComponent],
    }).compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(ChallengemanageComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
