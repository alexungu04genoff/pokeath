"""Small independent regression cases for continuous path certification."""
import unittest
import trimesh
from src.prototypes.validate_ulaula_sloped_assembly import swept_collision


class ContinuousTranslationTests(unittest.TestCase):
    def test_thin_obstacle_between_sample_positions(self):
        moving = trimesh.creation.box(extents=[.01,1,1])
        fixed = trimesh.creation.box(extents=[.01,1,1])
        fixed.apply_translation([.123,0,0])
        self.assertFalse(swept_collision(moving,fixed,[10,0,0])["passed"])

    def test_clear_parallel_motion(self):
        moving = trimesh.creation.box()
        fixed = trimesh.creation.box()
        fixed.apply_translation([2,2,0])
        self.assertTrue(swept_collision(moving,fixed,[10,0,0])["passed"])

    def test_seated_overlap_fails(self):
        cube = trimesh.creation.box()
        self.assertFalse(swept_collision(cube,cube,[10,0,0])["passed"])

    def test_nonconvex_clear_channel(self):
        bars=[]
        for y in [-2,2]:
            bar=trimesh.creation.box(extents=[10,1,1]); bar.apply_translation([0,y,0]); bars.append(bar)
        obstacle=trimesh.util.concatenate(bars)
        moving=trimesh.creation.box()
        self.assertTrue(swept_collision(moving,obstacle,[20,0,0])["passed"])


if __name__ == "__main__":
    unittest.main()
