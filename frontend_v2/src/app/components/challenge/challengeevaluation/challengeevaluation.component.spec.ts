import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { ChallengeevaluationComponent } from './challengeevaluation.component';
import { HttpClientModule } from '@angular/common/http';
import { RouterTestingModule } from '@angular/router/testing';

describe('ChallengeevaluationComponent', () => {
  let component: ChallengeevaluationComponent;
  let fixture: ComponentFixture<ChallengeevaluationComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ChallengeevaluationComponent],
      imports: [RouterTestingModule, HttpClientModule],
    }).compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(ChallengeevaluationComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

});
