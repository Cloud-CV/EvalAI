import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { ChallengediscussComponent } from './challengediscuss.component';

describe('ChallengediscussComponent', () => {
  let component: ChallengediscussComponent;
  let fixture: ComponentFixture<ChallengediscussComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ChallengediscussComponent],
    }).compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(ChallengediscussComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
