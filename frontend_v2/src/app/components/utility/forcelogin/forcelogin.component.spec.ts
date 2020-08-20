import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { ForceloginComponent } from './forcelogin.component';
import { GlobalService } from '../../../services/global.service';
import { AuthService } from '../../../services/auth.service';
import { ApiService } from '../../../services/api.service';
import { HttpClientModule } from '@angular/common/http';
import { RouterTestingModule } from '@angular/router/testing';

describe('ForceloginComponent', () => {
  let component: ForceloginComponent;
  let fixture: ComponentFixture<ForceloginComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ForceloginComponent],
      providers: [GlobalService, AuthService, ApiService],
      imports: [HttpClientModule, RouterTestingModule],
    }).compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(ForceloginComponent);
    component = fixture.componentInstance;
    component.path = '/challenges/me';
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
