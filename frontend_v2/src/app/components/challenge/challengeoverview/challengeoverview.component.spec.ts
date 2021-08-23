import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { ChallengeoverviewComponent } from './challengeoverview.component';
import { HttpClientModule } from '@angular/common/http';
import { RouterTestingModule } from '@angular/router/testing';

describe('ChallengeoverviewComponent', () => {
  let component: ChallengeoverviewComponent;
  let fixture: ComponentFixture<ChallengeoverviewComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ChallengeoverviewComponent],
      imports: [RouterTestingModule, HttpClientModule],
    }).compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(ChallengeoverviewComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
