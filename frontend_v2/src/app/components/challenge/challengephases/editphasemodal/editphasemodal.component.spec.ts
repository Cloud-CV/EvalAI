import { async, ComponentFixture, TestBed } from '@angular/core/testing';
import { NO_ERRORS_SCHEMA } from '@angular/core';
import { HttpClientModule } from '@angular/common/http';
import { EditphasemodalComponent } from './editphasemodal.component';
import { InputComponent } from '../../../utility/input/input.component';
import { GlobalService } from '../../../../services/global.service';
import { ChallengeService } from '../../../../services/challenge.service';
import { EndpointsService } from '../../../../services/endpoints.service';
import { ApiService } from '../../../../services/api.service';
import { AuthService } from '../../../../services/auth.service';

describe('EditphasemodalComponent', () => {
  let component: EditphasemodalComponent;
  let fixture: ComponentFixture<EditphasemodalComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [EditphasemodalComponent, InputComponent],
      providers: [GlobalService, ChallengeService, EndpointsService, ApiService, AuthService],
      imports: [HttpClientModule],
      schemas: [NO_ERRORS_SCHEMA],
    }).compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(EditphasemodalComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
